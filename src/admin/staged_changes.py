"""Changes made from the SQL console or the user page are held in one open
transaction until the teacher commits or rolls it back. A backup is taken
before the first change. The transaction lives in this process, so the app
must run as a single gunicorn worker (threads are fine)."""
import threading
import time
from typing import NamedTuple

from sqlalchemy.exc import SQLAlchemyError

from src import db
from src.admin import backups, sql_console

IDLE_SECONDS = 180
LOCK_TIMEOUT_MS = 5_000


class Step(NamedTuple):
    label: str
    rows: int


class Pending(NamedTuple):
    steps: tuple
    backup: str
    seconds_left: int


class NothingPending(Exception):
    """Commit or roll back was requested but no changes are staged."""


class _Open:
    def __init__(self, connection, transaction, backup):
        self.connection = connection
        self.transaction = transaction
        self.backup = backup
        self.steps = []
        self.deadline = 0.0
        self.timer = None


_lock = threading.RLock()
_open = None


def current():
    with _lock:
        if _open is None:
            return None
        return Pending(tuple(_open.steps), _open.backup,
                       max(0, round(_open.deadline - time.monotonic())))


def submit(sql, allow_write):
    """Route a console statement: reads run directly (or inside the pending
    transaction, so staged changes can be reviewed), changes are staged."""
    statement = sql_console.single_statement(sql)
    reading = sql_console.is_pure_read(statement) or (
        sql_console.is_read(statement) and not allow_write)
    if reading:
        return _review(statement) if current() else sql_console.run_read(statement)
    if not allow_write:
        sql_console.require_read_only(statement)
    return stage(statement)


def stage(statement, params=None, label=None):
    with _lock:
        started_here = _open is None
        if started_here:
            _begin()
        try:
            result = _execute(statement, params)
        except sql_console.QueryFailed:
            if started_here:
                _finish(commit=False)
            raise
        affected = result.rows_affected if result.rows_affected is not None else len(result.rows)
        _open.steps.append(Step(label or statement, affected))
        _touch()
        return result


def commit():
    return _end(commit=True)


def rollback():
    return _end(commit=False)


def _review(statement):
    with _lock:
        result = _execute(statement, None)
        _touch()
        return result


def _begin():
    global _open
    try:
        backup = backups.create()
    except SQLAlchemyError as error:
        raise sql_console.QueryFailed(f"Backup failed, nothing was changed: {error.orig or error}") from error
    connection = db.engine.connect()
    transaction = connection.begin()
    connection.exec_driver_sql(f"SET LOCAL statement_timeout = {sql_console.TIMEOUT_MS}")
    connection.exec_driver_sql(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}")
    _open = _Open(connection, transaction, backup)
    _touch()


def _execute(statement, params):
    """Run inside a savepoint so one failed statement doesn't poison the transaction."""
    savepoint = _open.connection.begin_nested()
    try:
        result = sql_console.execute(_open.connection, statement, params)
    except SQLAlchemyError as error:
        savepoint.rollback()
        raise sql_console.failure(error) from error
    savepoint.commit()
    return result


def _touch():
    _open.deadline = time.monotonic() + IDLE_SECONDS
    if _open.timer:
        _open.timer.cancel()
    _open.timer = threading.Timer(IDLE_SECONDS, _expire)
    _open.timer.daemon = True
    _open.timer.start()


def _expire():
    with _lock:
        if _open is not None and time.monotonic() >= _open.deadline - 0.05:
            _finish(commit=False)


def _end(commit):
    with _lock:
        if _open is None:
            raise NothingPending()
        return _finish(commit)


def _finish(commit):
    global _open
    finished, _open = _open, None
    finished.timer.cancel()
    try:
        finished.transaction.commit() if commit else finished.transaction.rollback()
    finally:
        finished.connection.close()
    return tuple(finished.steps)
