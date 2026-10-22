from datetime import datetime, timezone
from typing import NamedTuple

from sqlalchemy import text

from src import db

KEEP = 5
PREFIX = "backup_"
STAMP = "%Y%m%d_%H%M%S"


class Backup(NamedTuple):
    schema: str
    created_at: datetime
    bytes: int

    @property
    def restore_deleted_rows_sql(self):
        """Puts back rows that were deleted since this backup (rows are matched by id)."""
        return (f'INSERT INTO data SELECT * FROM "{self.schema}".data\n'
                "WHERE id NOT IN (SELECT id FROM data)")


def _quote(name):
    return db.engine.dialect.identifier_preparer.quote(name)


def list_backups():
    rows = db.session.execute(
        text(
            "SELECT n.nspname, COALESCE(SUM(pg_total_relation_size(c.oid)), 0) "
            "FROM pg_namespace n LEFT JOIN pg_class c ON c.relnamespace = n.oid AND c.relkind = 'r' "
            "WHERE n.nspname LIKE :pattern GROUP BY n.nspname ORDER BY n.nspname DESC"
        ),
        {"pattern": PREFIX.replace("_", "\\_") + "%"},
    ).all()
    return [
        Backup(name, datetime.strptime(name[len(PREFIX):], STAMP).replace(tzinfo=timezone.utc), int(size))
        for name, size in rows
    ]


def create(now=None):
    """Copy every table in the public schema into a new backup_<UTC time> schema
    on the same server, then drop all but the newest KEEP backups."""
    schema = PREFIX + (now or datetime.now(timezone.utc)).strftime(STAMP)
    with db.engine.begin() as connection:
        tables = connection.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        ).scalars().all()
        connection.exec_driver_sql(f"CREATE SCHEMA {_quote(schema)}")
        for table in tables:
            connection.exec_driver_sql(
                f"CREATE TABLE {_quote(schema)}.{_quote(table)} AS TABLE public.{_quote(table)}"
            )
    with db.engine.begin() as connection:
        for stale in list_backups()[KEEP:]:
            connection.exec_driver_sql(f"DROP SCHEMA {_quote(stale.schema)} CASCADE")
    return schema
