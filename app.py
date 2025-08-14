from flask import Flask, request, jsonify, redirect, url_for
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.environ.get("SPENDWISE_DB", "spendwise.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    expenses = conn.execute(
        "SELECT * FROM expenses ORDER BY date DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in expenses])


@app.route("/add", methods=["POST"])
def add_expense():
    data = request.get_json()
    if not data or "amount" not in data:
        return jsonify({"error": "amount required"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (amount, description, date) VALUES (?, ?, ?)",
        (data["amount"], data.get("description", ""), data.get("date", datetime.now().strftime("%Y-%m-%d"))),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "created"}), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
