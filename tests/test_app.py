import json
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
    rv = client.post("/add", json={
        "amount": 10.0,
        "description": "Lunch",
        "category_id": 1,
        "date": "2025-01-15",
    })
    assert rv.status_code == 201


def test_add_expense_missing_amount(client):
    rv = client.post("/add", json={"description": "no amount"})
    assert rv.status_code == 400


def test_add_expense_negative(client):
    rv = client.post("/add", json={"amount": -5})
    assert rv.status_code == 400


def test_delete_expense(client):
    client.post("/add", json={"amount": 5.0, "date": "2025-01-15"})
    rv = client.post("/delete/1")
    assert rv.status_code == 200
