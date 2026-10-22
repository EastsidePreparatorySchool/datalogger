import pytest

from src.admin import sql_console
from src.models.data import Data
from tests.test_routes import add_reading


def reading_count():
    return Data.query.count()


def test_select_returns_columns_and_rows(client):
    add_reading(client, device_id="a", temperature="21.5")

    result = sql_console.run("SELECT device_id, temperature FROM data")

    assert (result.columns, result.rows) == (["device_id", "temperature"], [["a", 21.5]])


def test_percent_and_cast_syntax_pass_through_untouched(client):
    result = sql_console.run("SELECT 'a%' LIKE 'a%' AS hit, 1::text AS n")

    assert result.rows == [[True, "1"]]


def test_non_primitive_values_are_shown_as_text(client):
    add_reading(client, device_id="a")

    value = sql_console.run("SELECT time_created FROM data").rows[0][0]

    assert isinstance(value, str)


@pytest.mark.parametrize("sql", [
    "DELETE FROM data",
    "drop table data",
    "-- note\nUPDATE data SET device_id = 'x'",
    "/* note */ INSERT INTO data (username) VALUES ('x')",
])
def test_writes_are_rejected_unless_allowed(client, sql):
    add_reading(client, device_id="a")

    with pytest.raises(sql_console.QueryRejected):
        sql_console.run(sql)

    assert reading_count() == 1


def test_leading_comment_before_select_is_allowed(client):
    assert sql_console.run("-- all of them\nSELECT 1 AS one").rows == [[1]]


def test_a_second_statement_cannot_smuggle_a_write(client):
    add_reading(client, device_id="a")

    with pytest.raises(sql_console.QueryRejected):
        sql_console.run("SELECT 1; COMMIT; DELETE FROM data")

    assert reading_count() == 1


def test_trailing_semicolon_is_fine(client):
    assert sql_console.run("SELECT 1 AS one;").rows == [[1]]


def test_database_refuses_writes_hidden_inside_a_select(client):
    add_reading(client, device_id="a")

    with pytest.raises(sql_console.QueryFailed, match="read-only"):
        sql_console.run("WITH gone AS (DELETE FROM data RETURNING id) SELECT * FROM gone")

    assert reading_count() == 1


def test_results_are_capped_and_marked_truncated(client):
    result = sql_console.run("SELECT generate_series(1, 5) AS n", max_rows=3)

    assert (len(result.rows), result.truncated) == (3, True)


def test_slow_queries_are_cancelled(client):
    with pytest.raises(sql_console.QueryFailed, match="timeout"):
        sql_console.run("SELECT pg_sleep(2)", timeout_ms=100)


def test_sql_errors_are_reported_and_the_session_stays_usable(client):
    with pytest.raises(sql_console.QueryFailed, match="does not exist"):
        sql_console.run("SELECT * FROM no_such_table")

    assert sql_console.run("SELECT 1 AS one").rows == [[1]]


def test_csv_export_neutralises_spreadsheet_formulas(client):
    add_reading(client, device_id="=HYPERLINK(1)")

    csv_text = sql_console.to_csv(sql_console.run("SELECT device_id FROM data"))

    assert csv_text.splitlines() == ["device_id", "'=HYPERLINK(1)"]


def test_every_example_query_runs(client):
    add_reading(client, device_id="a")

    for _title, sql in sql_console.EXAMPLES:
        sql_console.run(sql)


def test_console_page_shows_query_results(admin_client):
    from tests.conftest import csrf_token_from
    token = csrf_token_from(admin_client.get("/admin/sql"))

    page = admin_client.post("/admin/sql", data={
        "sql": "SELECT 42 AS answer", "csrf_token": token, "action": "run",
    }).get_data(as_text=True)

    assert "<th>answer</th>" in page and ">42<" in page


def test_console_can_download_csv(admin_client):
    from tests.conftest import csrf_token_from
    token = csrf_token_from(admin_client.get("/admin/sql"))

    response = admin_client.post("/admin/sql", data={
        "sql": "SELECT 42 AS answer", "csrf_token": token, "action": "csv",
    })

    assert (response.mimetype, response.get_data(as_text=True).splitlines()) == (
        "text/csv", ["answer", "42"])
