from flask import Flask, request, jsonify, render_template, redirect, url_for
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
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return render_template("index.html", expenses=expenses, categories=categories)


@app.route("/add", methods=["POST"])
def add_expense():
    amount = request.form.get("amount", type=float)
    description = request.form.get("description", "").strip()
    category_id = request.form.get("category_id", type=int)
    date = request.form.get("date", datetime.now().strftime("%Y-%m-%d"))

    if not amount or amount <= 0:
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (amount, description, category_id, date) VALUES (?, ?, ?, ?)",
        (amount, description, category_id, date),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/summary")
def summary():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    conn = get_db()
    rows = conn.execute("""
        SELECT c.name, c.color, COALESCE(SUM(e.amount), 0) as total
        FROM categories c
        LEFT JOIN expenses e ON e.category_id = c.id
            AND strftime('%%Y-%%m', e.date) = ?
        GROUP BY c.id
        HAVING total > 0
        ORDER BY total DESC
    """, (month,)).fetchall()
    grand_total = sum(r["total"] for r in rows)
    conn.close()
    return render_template("summary.html", rows=rows, month=month, grand_total=grand_total)


@app.route("/api/expenses", methods=["GET"])
def api_list_expenses():
    conn = get_db()
    month = request.args.get("month")
    if month:
        expenses = conn.execute("""
            SELECT e.*, c.name as category_name
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE strftime('%%Y-%%m', e.date) = ?
            ORDER BY e.date DESC
        """, (month,)).fetchall()
    else:
        expenses = conn.execute("""
            SELECT e.*, c.name as category_name
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            ORDER BY e.date DESC
            LIMIT 100
        """).fetchall()
    conn.close()
    return jsonify([dict(row) for row in expenses])


@app.route("/api/expenses", methods=["POST"])
def api_add_expense():
    data = request.get_json()
    if not data or "amount" not in data:
        return jsonify({"error": "amount is required"}), 400

    amount = data["amount"]
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    description = data.get("description", "")
    category_id = data.get("category_id")
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO expenses (amount, description, category_id, date) VALUES (?, ?, ?, ?)",
        (amount, description, category_id, date),
    )
    expense_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": expense_id, "status": "created"}), 201


@app.route("/api/summary/<month>")
def api_summary(month):
    conn = get_db()
    rows = conn.execute("""
        SELECT c.name as category, COALESCE(SUM(e.amount), 0) as total
        FROM categories c
        LEFT JOIN expenses e ON e.category_id = c.id
            AND strftime('%%Y-%%m', e.date) = ?
        GROUP BY c.id
        HAVING total > 0
        ORDER BY total DESC
    """, (month,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
