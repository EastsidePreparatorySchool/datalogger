import time

import pytest
from sqlalchemy import text

from src import db
from src.admin import backups, sql_console, staged_changes
from tests.conftest import csrf_token_from
from tests.test_routes import add_reading


def visible_to_everyone():
    """Count rows as another connection (so uncommitted changes are invisible)."""
    with db.engine.connect() as other:
        return other.execute(text("SELECT count(*) FROM data")).scalar()


def test_a_change_is_invisible_to_others_until_committed(client):
    add_reading(client, device_id="a")

    result = staged_changes.submit("DELETE FROM data", allow_write=True)

    assert (result.rows_affected, visible_to_everyone()) == (1, 1)
    staged_changes.commit()
    assert visible_to_everyone() == 0


def test_rolling_back_leaves_the_data_untouched(client):
    add_reading(client, device_id="a")
    staged_changes.submit("DELETE FROM data", allow_write=True)

    staged_changes.rollback()

    assert (visible_to_everyone(), staged_changes.current()) == (1, None)


def test_selects_during_review_see_the_staged_state(client):
    add_reading(client, device_id="a")
    staged_changes.submit("DELETE FROM data", allow_write=True)

    assert staged_changes.submit("SELECT count(*) FROM data", allow_write=False).rows == [[0]]


def test_plain_selects_do_not_stage_anything_or_back_up(client):
    staged_changes.submit("SELECT 1", allow_write=True)
    staged_changes.submit("SELECT 1", allow_write=False)

    assert (staged_changes.current(), backups.list_backups()) == (None, [])


def test_changes_are_refused_without_allow_write(client):
    with pytest.raises(sql_console.QueryRejected):
        staged_changes.submit("DELETE FROM data", allow_write=False)

    assert (staged_changes.current(), backups.list_backups()) == (None, [])


def test_first_change_takes_a_backup_holding_the_original_data(client):
    add_reading(client, device_id="a")

    staged_changes.submit("DELETE FROM data", allow_write=True)
    staged_changes.commit()

    (backup,) = backups.list_backups()
    assert db.session.execute(text(f'SELECT count(*) FROM "{backup.schema}".data')).scalar() == 1


def test_further_changes_join_the_pending_transaction_with_one_backup(client):
    add_reading(client, device_id="a")
    add_reading(client, device_id="b")

    staged_changes.submit("DELETE FROM data WHERE device_id = 'a'", allow_write=True)
    staged_changes.submit("DELETE FROM data WHERE device_id = 'b'", allow_write=True)

    pending = staged_changes.current()
    assert ([s.rows for s in pending.steps], len(backups.list_backups())) == ([1, 1], 1)


def test_a_failed_statement_is_dropped_but_earlier_changes_survive(client):
    add_reading(client, device_id="a")
    staged_changes.submit("DELETE FROM data", allow_write=True)

    with pytest.raises(sql_console.QueryFailed):
        staged_changes.submit("UPDATE nope SET x = 1", allow_write=True)

    assert len(staged_changes.current().steps) == 1
    assert staged_changes.submit("SELECT count(*) FROM data", allow_write=False).rows == [[0]]


def test_a_failing_first_statement_leaves_nothing_pending(client):
    with pytest.raises(sql_console.QueryFailed):
        staged_changes.submit("UPDATE nope SET x = 1", allow_write=True)

    assert staged_changes.current() is None


def test_a_with_statement_counts_as_a_change_when_changes_are_allowed(client):
    add_reading(client, device_id="a")

    staged_changes.submit("WITH gone AS (DELETE FROM data RETURNING id) SELECT * FROM gone", allow_write=True)

    assert (len(staged_changes.current().steps), visible_to_everyone()) == (1, 1)


def test_commit_or_rollback_with_nothing_pending_is_an_error(client):
    with pytest.raises(staged_changes.NothingPending):
        staged_changes.commit()


def test_forgotten_changes_roll_back_on_their_own(client, monkeypatch):
    monkeypatch.setattr(staged_changes, "IDLE_SECONDS", 0.1)
    add_reading(client, device_id="a")
    staged_changes.submit("DELETE FROM data", allow_write=True)

    time.sleep(0.5)

    assert (staged_changes.current(), visible_to_everyone()) == (None, 1)


def test_user_page_stages_deletion_of_only_that_users_readings(admin_client):
    add_reading(admin_client, device_id="a")
    admin_client.post("/api/data/other/add", query_string={"device_id": "z"})
    token = csrf_token_from(admin_client.get("/admin/users/jbriggs"))

    admin_client.post("/admin/users/jbriggs/delete", data={"csrf_token": token})
    assert visible_to_everyone() == 2

    admin_client.post("/admin/pending/commit", data={"csrf_token": token})
    remaining = db.session.execute(text("SELECT username FROM data")).scalars().all()
    assert remaining == ["other"]


def test_console_page_shows_the_pending_panel_and_can_roll_back(admin_client):
    add_reading(admin_client, device_id="a")
    token = csrf_token_from(admin_client.get("/admin/sql"))
    admin_client.post("/admin/sql", data={
        "sql": "DELETE FROM data", "allow_write": "on", "csrf_token": token, "action": "run"})

    page = admin_client.get("/admin/sql").get_data(as_text=True)
    assert "1 change(s) staged" in page and "Commit changes" in page

    admin_client.post("/admin/pending/rollback", data={"csrf_token": token})
    assert (staged_changes.current(), visible_to_everyone()) == (None, 1)
