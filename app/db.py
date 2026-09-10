import os
import sqlite3
from datetime import datetime, date

_INITIALIZED = False


def get_db_path():
    if os.environ.get("VERCEL"):
        return "/tmp/laparsmart.db"
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_dir = os.path.join(base, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    return os.path.join(instance_dir, "laparsmart.db")


def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS staff (
    staff_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS admin (
    admin_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS menu_item (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    available_date TEXT NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id TEXT NOT NULL,
    order_type TEXT NOT NULL DEFAULT 'Counter',
    status TEXT NOT NULL DEFAULT 'Pending',
    total_amount REAL NOT NULL DEFAULT 0,
    order_date TEXT NOT NULL,
    meeting_room TEXT,
    meeting_time TEXT,
    FOREIGN KEY (staff_id) REFERENCES staff (staff_id)
);

CREATE TABLE IF NOT EXISTS order_item (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (order_id),
    FOREIGN KEY (item_id) REFERENCES menu_item (item_id)
);

CREATE TABLE IF NOT EXISTS notification (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    sent_time TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (order_id) REFERENCES orders (order_id)
);
"""


def seed(conn):
    today = date.today().isoformat()

    staff = [
        ("S001", "Ahmad Zaki", "Marketing Division"),
        ("S002", "Nur Aina", "Finance Division"),
        ("S003", "Ravi Kumar", "IT Division"),
    ]
    conn.executemany(
        "INSERT INTO staff (staff_id, name, department, active) VALUES (?, ?, ?, 1)",
        staff,
    )

    admins = [("A001", "Admin Farah", "Cafe Admin")]
    conn.executemany(
        "INSERT INTO admin (admin_id, name, role, active) VALUES (?, ?, ?, 1)",
        admins,
    )

    menu = [
        ("Nasi Lemak Ayam", 6.50, "Food", today),
        ("Mee Goreng Mamak", 5.00, "Food", today),
        ("Roti Canai", 1.80, "Food", today),
        ("Fried Chicken Set", 8.50, "Food", today),
        ("Teh Tarik", 2.00, "Beverage", today),
        ("Kopi O", 1.50, "Beverage", today),
        ("Iced Milo", 2.50, "Beverage", today),
    ]
    conn.executemany(
        "INSERT INTO menu_item (name, price, category, available_date, is_available) VALUES (?, ?, ?, ?, 1)",
        menu,
    )
    conn.commit()


def init_db():
    global _INITIALIZED
    if _INITIALIZED:
        return
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    row = conn.execute("SELECT COUNT(*) AS c FROM menu_item").fetchone()
    if row["c"] == 0:
        seed(conn)
    conn.close()
    _INITIALIZED = True


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return date.today().isoformat()
