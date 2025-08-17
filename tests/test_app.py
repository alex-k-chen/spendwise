import os
import tempfile
import pytest
from app import app, init_db


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app.config["TESTING"] = True
    os.environ["SPENDWISE_DB"] = db_path
    import app as app_module
    app_module.DB_PATH = db_path
    init_db()
    with app.test_client() as client:
        yield client
    os.close(db_fd)
    os.unlink(db_path)


def test_index(client):
    rv = client.get("/")
    assert rv.status_code == 200


def test_add_expense(client):
    rv = client.post("/add", json={"amount": 10.0, "description": "Test"})
    assert rv.status_code == 201
