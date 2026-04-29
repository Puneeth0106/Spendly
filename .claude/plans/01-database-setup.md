# Implementation Plan — 01 Database Setup

## Goal

Implement the SQLite data layer for Spendly by replacing the stub in `database/db.py` and wiring `init_db()` + `seed_db()` into `app.py` startup. Outcome: app launches, creates `spendly.db` if missing, applies schema for `users` and `expenses`, and seeds one demo user with 8 sample expenses idempotently.

---

## Current State

- `database/db.py` — empty stub with comments only; no functions implemented.
- `app.py` — Flask app with landing/register/login/terms/privacy routes and placeholder routes for logout/profile/expenses. No DB wiring, no imports from `database`.
- No `spendly.db` file exists yet (will be created on first startup).
- `werkzeug` is available (Flask dependency); `sqlite3` is stdlib.

---

## Files to Change

1. `database/db.py` — implement `get_db()`, `init_db()`, `seed_db()`.
2. `app.py` — import the three functions, call `init_db()` + `seed_db()` inside `app.app_context()` at startup.

No new files, no new dependencies.

---

## Step 1 — Implement `database/db.py`

### 1a. Imports

```python
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from werkzeug.security import generate_password_hash
```

### 1b. Database path

Resolve `spendly.db` to project root (parent of the `database/` package) so the file lives next to `app.py` regardless of CWD:

```python
DB_PATH = Path(__file__).resolve().parent.parent / "spendly.db"
```

### 1c. `get_db()`

- Open `sqlite3.connect(DB_PATH)`.
- Set `conn.row_factory = sqlite3.Row` for dict-like row access.
- Execute `PRAGMA foreign_keys = ON` on the connection (must be set per-connection, not once globally).
- Return the connection. Caller is responsible for closing.

### 1d. `init_db()`

- Call `get_db()`, then issue two `CREATE TABLE IF NOT EXISTS` statements matching the spec schema:
  - `users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')))`
  - `expenses(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, date TEXT NOT NULL, description TEXT, created_at TEXT DEFAULT (datetime('now')), FOREIGN KEY (user_id) REFERENCES users(id))`
- `commit()` and `close()`.
- Idempotent: safe on every startup because of `IF NOT EXISTS`.

### 1e. `seed_db()`

- Open connection.
- `SELECT COUNT(*) FROM users`. If result > 0, `close()` and return — prevents duplicate seeds.
- Insert demo user with parameterized query:
  - name = `Demo User`
  - email = `demo@spendly.com`
  - password_hash = `generate_password_hash("demo123")`
- Capture `cursor.lastrowid` as `user_id`.
- Insert 8 sample expenses (parameterized, in a single `executemany`), spread across the current month and covering each of the 7 fixed categories at least once (the 8th can repeat any category). Use `date.today().replace(day=...)` to keep dates within the current month, formatted `YYYY-MM-DD`. Suggested set:

  | # | category | amount | day-of-month | description |
  |---|---|---|---|---|
  | 1 | Food | 12.50 | 2 | Lunch |
  | 2 | Transport | 25.00 | 4 | Bus pass |
  | 3 | Bills | 80.00 | 6 | Internet |
  | 4 | Health | 45.00 | 9 | Pharmacy |
  | 5 | Entertainment | 18.99 | 12 | Movie ticket |
  | 6 | Shopping | 60.00 | 15 | Clothes |
  | 7 | Other | 10.00 | 18 | Misc |
  | 8 | Food | 22.40 | 22 | Groceries |

  Day-of-month values must be clamped to the current month's length to avoid `ValueError` on short months — use `min(day, last_day_of_month)` or pre-compute via `calendar.monthrange`.

- `commit()` and `close()`.

### 1f. Implementation rules (from spec §11)

- Parameterized queries only (`?` placeholders); never f-strings or `%` formatting in SQL.
- `amount` stored as REAL.
- Always enable `PRAGMA foreign_keys = ON` inside `get_db()`.
- Dates always `YYYY-MM-DD`.

---

## Step 2 — Wire startup in `app.py`

Add at the top, after `from flask import ...`:

```python
from database.db import get_db, init_db, seed_db
```

(`get_db` is imported now even though it isn't used yet, because subsequent steps will need it and the spec §6 lists it.)

After `app = Flask(__name__)`, add:

```python
with app.app_context():
    init_db()
    seed_db()
```

This runs once at import time, before the first request, and is idempotent on restart.

---

## Step 3 — Verification

Run from project root:

1. `python app.py` — app should boot on port 5001 with no errors. `spendly.db` should appear in the project root.
2. Inspect schema:
   ```
   sqlite3 spendly.db ".schema"
   sqlite3 spendly.db "SELECT COUNT(*) FROM users;"   # expect 1
   sqlite3 spendly.db "SELECT COUNT(*) FROM expenses;" # expect 8
   sqlite3 spendly.db "SELECT DISTINCT category FROM expenses;" # expect 7 categories
   ```
3. Restart the app — counts should remain 1 and 8 (no duplicate seed).
4. Constraint checks (sanity):
   ```
   sqlite3 spendly.db "INSERT INTO users(name,email,password_hash) VALUES('x','demo@spendly.com','y');"
   # expect: UNIQUE constraint failed: users.email
   sqlite3 spendly.db "PRAGMA foreign_keys=ON; INSERT INTO expenses(user_id,amount,category,date) VALUES(999,1,'Food','2026-04-29');"
   # expect: FOREIGN KEY constraint failed
   ```

---

## Risks & Edge Cases

- **Per-connection PRAGMA**: `PRAGMA foreign_keys` is not persistent — every `get_db()` must set it, otherwise FK enforcement silently disables in later steps.
- **Day-of-month overflow**: hardcoding day 31 fails in months with fewer days. Clamp to `monthrange(...)[1]`.
- **Module-import side effects**: calling `init_db()`/`seed_db()` at import time means tests that import `app` will create/seed the DB. Acceptable for this stage; later steps can move this behind a `create_app()` factory or a CLI command if needed.
- **Connection lifetime**: each helper opens and closes its own connection. Future request-scoped pooling (e.g., Flask `g`) is out of scope for this step.
- **Password hash algorithm**: `generate_password_hash` defaults are fine; do not pin a method here, so future Werkzeug upgrades stay compatible with `check_password_hash`.

---

## Definition of Done (from spec §14)

- [ ] `spendly.db` created on app startup
- [ ] `users` and `expenses` tables exist with correct columns/constraints
- [ ] Demo user (`demo@spendly.com`) exists with hashed password
- [ ] 8 sample expenses across all 7 categories
- [ ] Re-running app does not duplicate seed data
- [ ] App starts without errors on port 5001
- [ ] FK enforcement verified
- [ ] All inserts/queries use `?` parameter binding