from flask import Flask, request, jsonify, redirect, url_for
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.environ.get("SPENDWISE_DB", "spendwise.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#6b7280'
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            description TEXT,
            category_id INTEGER,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
    """)
    cur = conn.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        defaults = [
            ("Food & Dining", "#ef4444"),
            ("Transport", "#3b82f6"),
            ("Housing", "#8b5cf6"),
            ("Entertainment", "#f59e0b"),
            ("Utilities", "#10b981"),
            ("Shopping", "#ec4899"),
            ("Health", "#06b6d4"),
            ("Other", "#6b7280"),
        ]
        conn.executemany("INSERT INTO categories (name, color) VALUES (?, ?)", defaults)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    expenses = conn.execute("""
        SELECT e.*, c.name as category_name, c.color as category_color
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        ORDER BY e.date DESC, e.created_at DESC
        LIMIT 50
    """).fetchall()
    conn.close()
    return jsonify([dict(row) for row in expenses])


@app.route("/add", methods=["POST"])
def add_expense():
    data = request.get_json()
    if not data or "amount" not in data:
        return jsonify({"error": "amount required"}), 400

    amount = data["amount"]
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (amount, description, category_id, date) VALUES (?, ?, ?, ?)",
        (amount, data.get("description", ""), data.get("category_id"), data.get("date", datetime.now().strftime("%Y-%m-%d"))),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "created"}), 201


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
