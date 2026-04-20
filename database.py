import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        consent INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        method TEXT,
        details TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        rating INTEGER,
        comment TEXT,
        anonymous INTEGER,
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS appeals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(user_id, username):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_pending_withdrawals_count(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM withdrawals WHERE user_id = ? AND status = 'pending'", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def add_withdrawal(user_id, amount, method, details):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO withdrawals (user_id, amount, method, details, created_at) VALUES (?, ?, ?, ?, ?)",
              (user_id, amount, method, details, datetime.now()))
    conn.commit()
    conn.close()

def get_user_withdrawals(user_id, page=0, per_page=8):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    offset = page * per_page
    c.execute("SELECT id, amount, method, status, created_at FROM withdrawals WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
              (user_id, per_page, offset))
    withdrawals = c.fetchall()
    c.execute("SELECT COUNT(*) FROM withdrawals WHERE user_id = ?", (user_id,))
    total = c.fetchone()[0]
    conn.close()
    return withdrawals, total

def save_review(user_id, rating, comment, anonymous):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO reviews (user_id, rating, comment, anonymous, created_at) VALUES (?, ?, ?, ?, ?)",
              (user_id, rating, comment, anonymous, datetime.now()))
    conn.commit()
    conn.close()

def save_appeal(user_id, message):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO appeals (user_id, message, created_at) VALUES (?, ?, ?)",
              (user_id, message, datetime.now()))
    conn.commit()
    conn.close()

def get_all_withdrawals(status=None):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    if status:
        c.execute("SELECT id, user_id, amount, method, details, status, created_at FROM withdrawals WHERE status = ? ORDER BY created_at DESC", (status,))
    else:
        c.execute("SELECT id, user_id, amount, method, details, status, created_at FROM withdrawals ORDER BY created_at DESC")
    data = c.fetchall()
    conn.close()
    return data

def get_all_appeals():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, user_id, message, status, created_at FROM appeals WHERE status = 'pending' ORDER BY created_at DESC")
    data = c.fetchall()
    conn.close()
    return data

def update_withdrawal_status(withdrawal_id, status):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE withdrawals SET status = ? WHERE id = ?", (status, withdrawal_id))
    conn.commit()
    conn.close()

def update_appeal_status(appeal_id, status):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE appeals SET status = ? WHERE id = ?", (status, appeal_id))
    conn.commit()
    conn.close()

def get_last_withdrawals(user_id, limit=5):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT amount, status, created_at FROM withdrawals WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
    data = c.fetchall()
    conn.close()
    return data

def set_consent(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET consent = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def check_consent(user_id):
    user = get_user(user_id)
    return user[4] if user else 0

def ban_user(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return user[3] if user else 0

def get_user_by_username(username):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT user_id, username, balance FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

init_db()
