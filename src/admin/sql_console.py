import csv
import io
import re
import time
from typing import NamedTuple, Optional

from sqlalchemy.exc import SQLAlchemyError

from src import db

MAX_ROWS = 500
TIMEOUT_MS = 10_000

READ_ONLY_STARTS = frozenset({"select", "with", "values", "table", "show", "explain"})
# WITH can wrap a DELETE or INSERT, so it only counts as a read when changes are not allowed.
PURE_READ_STARTS = READ_ONLY_STARTS - {"with"}
LEADING_COMMENTS = re.compile(r"^(\s|--[^\n]*(\n|$)|/\*.*?\*/)*", re.DOTALL)
FORMULA_STARTS = ("=", "+", "-", "@")

EXAMPLES = (
    ("Latest 50 readings",
     "SELECT * FROM data ORDER BY time_created DESC LIMIT 50"),
    ("Readings per user",
     "SELECT username, count(*) AS readings, max(time_created) AS last_post\n"
     "FROM data GROUP BY username ORDER BY readings DESC"),
    ("Busiest users, last hour",
     "SELECT username, count(*) AS readings FROM data\n"
     "WHERE time_created > now() - interval '1 hour'\n"
     "GROUP BY username ORDER BY readings DESC"),
    ("Users writing to many devices",
     "SELECT username, count(DISTINCT device_id) AS devices FROM data\n"
     "GROUP BY username HAVING count(DISTINCT device_id) > 5 ORDER BY devices DESC"),
    ("Readings with no device_id",
     "SELECT username, count(*) AS readings FROM data\n"
     "WHERE device_id IS NULL GROUP BY username ORDER BY readings DESC"),
    ("Readings per day",
     "SELECT date(time_created) AS day, count(*) AS readings FROM data\n"
     "GROUP BY day ORDER BY day DESC"),
    ("Table sizes",
     "SELECT relname AS table, pg_size_pretty(pg_total_relation_size(relid)) AS size\n"
     "FROM pg_stat_user_tables WHERE schemaname = 'public'\n"
     "ORDER BY pg_total_relation_size(relid) DESC"),
)


class QueryRejected(ValueError):
    """The text was refused before it reached the database."""


class QueryFailed(Exception):
    """The database refused or aborted the statement."""


class QueryResult(NamedTuple):
    columns: list
    rows: list
    truncated: bool
    elapsed_ms: int
    rows_affected: Optional[int]


def single_statement(sql):
    statement = re.sub(r"[;\s]+$", "", sql or "")
    if not statement.strip():
        raise QueryRejected("Enter a query to run.")
    if ";" in statement:
        raise QueryRejected("Run one statement at a time (a ';' appears inside the query).")
    return statement.strip()


def first_word(statement):
    return re.match(r"\w*", LEADING_COMMENTS.sub("", statement)).group().lower()


def is_read(statement):
    return first_word(statement) in READ_ONLY_STARTS


def is_pure_read(statement):
    return first_word(statement) in PURE_READ_STARTS


def require_read_only(statement):
    if not is_read(statement):
        raise QueryRejected(
            "Only SELECT-style queries run directly. Tick \"Allow changes\" to stage anything else for review."
        )


def failure(error):
    return QueryFailed(str(getattr(error, "orig", error)).strip())


def display_value(value):
    return value if value is None or isinstance(value, (int, float, str)) else str(value)


def execute(connection, statement, params=None, max_rows=MAX_ROWS):
    """Run one statement on a connection the caller manages. Text typed by the
    teacher (params=None) has its % escaped so psycopg2 leaves it alone."""
    started = time.perf_counter()
    if params is None:
        cursor = connection.exec_driver_sql(statement.replace("%", "%%"))
    else:
        cursor = connection.exec_driver_sql(statement, params)
    if cursor.returns_rows:
        fetched = cursor.fetchmany(max_rows + 1)
        columns = list(cursor.keys())
        rows = [[display_value(v) for v in row] for row in fetched[:max_rows]]
        truncated, affected = len(fetched) > max_rows, None
    else:
        columns, rows, truncated, affected = [], [], False, cursor.rowcount
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    return QueryResult(columns, rows, truncated, elapsed_ms, affected)


def run_read(statement, max_rows=MAX_ROWS, timeout_ms=TIMEOUT_MS):
    """Execute in a read-only transaction, so the database itself refuses
    writes even if the text check were fooled."""
    try:
        connection = db.session.connection()
        connection.exec_driver_sql(f"SET LOCAL statement_timeout = {int(timeout_ms)}")
        connection.exec_driver_sql("SET LOCAL transaction_read_only = on")
        return execute(connection, statement, max_rows=max_rows)
    except SQLAlchemyError as error:
        raise failure(error) from error
    finally:
        db.session.rollback()


def run(sql, max_rows=MAX_ROWS, timeout_ms=TIMEOUT_MS):
    statement = single_statement(sql)
    require_read_only(statement)
    return run_read(statement, max_rows, timeout_ms)


def _spreadsheet_safe(value):
    """Stop students' text from running as a formula when opened in Excel."""
    if isinstance(value, str) and value.startswith(FORMULA_STARTS):
        return "'" + value
    return value


def to_csv(result):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(result.columns)
    writer.writerows([[_spreadsheet_safe(v) for v in row] for row in result.rows])
    return out.getvalue()
