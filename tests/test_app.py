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


def test_index_empty(client):
    rv = client.get("/")
    assert rv.status_code == 200
    assert b"spendwise" in rv.data


def test_add_expense(client):
    rv = client.post("/add", data={
        "amount": "12.50",
        "description": "Coffee",
        "category_id": "1",
        "date": "2025-01-15",
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b"Coffee" in rv.data


def test_add_expense_invalid(client):
    rv = client.post("/add", data={
        "amount": "",
        "description": "Bad",
    }, follow_redirects=True)
    assert rv.status_code == 200


def test_delete_expense(client):
    client.post("/add", data={
        "amount": "5.00",
        "description": "Snack",
        "category_id": "1",
        "date": "2025-01-15",
    })
    rv = client.post("/delete/1", follow_redirects=True)
    assert rv.status_code == 200


def test_api_add_expense(client):
    rv = client.post("/api/expenses", json={
        "amount": 42.0,
        "description": "Test API",
        "category_id": 1,
        "date": "2025-02-01",
    })
    assert rv.status_code == 201
    data = json.loads(rv.data)
    assert data["status"] == "created"


def test_api_add_expense_missing_amount(client):
    rv = client.post("/api/expenses", json={"description": "no amount"})
    assert rv.status_code == 400


def test_api_add_expense_negative(client):
    rv = client.post("/api/expenses", json={"amount": -5})
    assert rv.status_code == 400


def test_api_list_expenses(client):
    client.post("/api/expenses", json={
        "amount": 10.0,
        "description": "Lunch",
        "date": "2025-03-10",
    })
    rv = client.get("/api/expenses?month=2025-03")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data) == 1
    assert data[0]["description"] == "Lunch"


def test_summary_page(client):
    client.post("/add", data={
        "amount": "20.00",
        "description": "Groceries",
        "category_id": "1",
        "date": "2025-01-15",
    })
    rv = client.get("/summary?month=2025-01")
    assert rv.status_code == 200
    assert b"20.00" in rv.data


def test_api_summary(client):
    client.post("/api/expenses", json={
        "amount": 30.0,
        "category_id": 1,
        "date": "2025-04-01",
    })
    rv = client.get("/api/summary/2025-04")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data) >= 1


def test_export_csv(client):
    client.post("/add", data={
        "amount": "15.00",
        "description": "Export test",
        "category_id": "2",
        "date": "2025-05-01",
    })
    rv = client.get("/export")
    assert rv.status_code == 200
    assert rv.content_type == "text/csv; charset=utf-8"
    assert b"Export test" in rv.data
