import pytest

from src import db, init_app
from src.admin import backups, staged_changes

ADMIN_PASSWORD = "teacher-pw"


@pytest.fixture
def app():
    app = init_app()
    app.config["ADMIN_PASSWORD"] = ADMIN_PASSWORD
    with app.app_context():
        clean_slate()
        db.create_all()
        yield app
        clean_slate()
        db.session.remove()


def clean_slate():
    """Release any staged transaction (its locks would block drop_all) and old backups."""
    try:
        staged_changes.rollback()
    except staged_changes.NothingPending:
        pass
    for backup in backups.list_backups():
        db.session.execute(db.text(f'DROP SCHEMA "{backup.schema}" CASCADE'))
    db.session.commit()
    db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    """A client that has already logged in to /admin."""
    client.post("/admin/login", data={
        "password": ADMIN_PASSWORD,
        "csrf_token": csrf_token_from(client.get("/admin/login")),
    })
    return client


def csrf_token_from(response):
    page = response.get_data(as_text=True)
    return page.split('name="csrf_token" value="')[1].split('"')[0]
