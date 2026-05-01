import calendar
import sqlite3
from datetime import date
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent.parent / "spendly.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing > 0:
            return

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (
                "Demo User",
                "demo@spendly.com",
                generate_password_hash("demo123"),
            ),
        )
        user_id = cursor.lastrowid

        today = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]

        def d(day):
            return date(today.year, today.month, min(day, last_day)).isoformat()

        sample_expenses = [
            (user_id, 12.50, "Food", d(2), "Lunch"),
            (user_id, 25.00, "Transport", d(4), "Bus pass"),
            (user_id, 80.00, "Bills", d(6), "Internet"),
            (user_id, 45.00, "Health", d(9), "Pharmacy"),
            (user_id, 18.99, "Entertainment", d(12), "Movie ticket"),
            (user_id, 60.00, "Shopping", d(15), "Clothes"),
            (user_id, 10.00, "Other", d(18), "Misc"),
            (user_id, 22.40, "Food", d(22), "Groceries"),
        ]

        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            sample_expenses,
        )
        conn.commit()
    finally:
        conn.close()
