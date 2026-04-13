import sqlite3
import os
import time

DB_PATH = os.path.join(os.getenv("DATA_DIR", "data"), "niftywall.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    import json
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        username TEXT,
        action TEXT,
        details TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS uptime_history (
        date TEXT PRIMARY KEY,
        uptime REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS brute_force (
        ip TEXT PRIMARY KEY,
        attempts INTEGER,
        last_attempt REAL
    )''')
    
    # --- Migration from JSON ---
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        json_users = os.path.join(os.path.dirname(DB_PATH), "users.json")
        if os.path.exists(json_users):
            try:
                with open(json_users, 'r') as f:
                    users = json.load(f)
                    for uname, udata in users.items():
                        c.execute('INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)',
                                  (uname, udata['password'], udata.get('created_at', '2026-04-13T00:00:00')))
                print("Migrated users from JSON to SQLite")
            except: pass
            
    conn.commit()
    conn.close()

init_db()
