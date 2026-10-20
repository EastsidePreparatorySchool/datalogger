import pytest

from src import db, init_app


@pytest.fixture
def client():
    app = init_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()
        db.session.remove()
