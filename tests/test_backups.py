from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from src import db
from src.admin import backups
from tests.test_routes import add_reading

T0 = datetime(2026, 10, 22, 15, 30, 12, tzinfo=timezone.utc)


def rows_in(schema):
    return db.session.execute(text(f'SELECT count(*) FROM "{schema}".data')).scalar()


def test_backup_copies_the_tables_into_a_timestamped_schema(client):
    add_reading(client, device_id="a")

    schema = backups.create(now=T0)

    assert (schema, rows_in(schema)) == ("backup_20261022_153012", 1)


def test_backup_is_unaffected_by_later_changes(client):
    add_reading(client, device_id="a")
    schema = backups.create(now=T0)

    db.session.execute(text("DELETE FROM data"))
    db.session.commit()

    assert rows_in(schema) == 1


def test_backups_are_listed_newest_first_with_their_time_and_size(client):
    add_reading(client, device_id="a")
    backups.create(now=T0)
    backups.create(now=T0 + timedelta(minutes=5))

    newest, oldest = backups.list_backups()

    assert (newest.created_at, oldest.created_at) == (T0 + timedelta(minutes=5), T0)
    assert oldest.bytes > 0


def test_only_the_newest_backups_are_kept(client):
    for minute in range(backups.KEEP + 2):
        backups.create(now=T0 + timedelta(minutes=minute))

    kept = [b.created_at for b in backups.list_backups()]

    assert kept == [T0 + timedelta(minutes=m) for m in range(backups.KEEP + 1, 1, -1)]


def test_restore_statement_puts_back_deleted_rows_only(client):
    add_reading(client, device_id="a")
    add_reading(client, device_id="b")
    (backup,) = [backups.create(now=T0)] and backups.list_backups()
    db.session.execute(text("DELETE FROM data WHERE device_id = 'a'"))
    db.session.commit()

    db.session.execute(text(backup.restore_deleted_rows_sql))
    db.session.commit()

    assert sorted(r[0] for r in db.session.execute(text("SELECT device_id FROM data"))) == ["a", "b"]


def test_dashboard_lists_backups_and_can_make_one(admin_client):
    from tests.conftest import csrf_token_from
    token = csrf_token_from(admin_client.get("/admin/"))

    admin_client.post("/admin/backups", data={"csrf_token": token})

    assert len(backups.list_backups()) == 1
    assert "Restore deleted rows" in admin_client.get("/admin/").get_data(as_text=True)
