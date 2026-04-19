import json
import os
from datetime import datetime, timedelta

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

USERS_FILE = f"{DATA_FOLDER}/users.json"
ACTUAL_FILE = f"{DATA_FOLDER}/actual_list.json"
SUPPORT_FILE = f"{DATA_FOLDER}/supports.json"
SELL_ORDERS_FILE = f"{DATA_FOLDER}/sell_orders.json"
BANNED_FILE = f"{DATA_FOLDER}/banned.json"

def load_json(file, default):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():
    return load_json(USERS_FILE, [])

def save_users(users):
    save_json(USERS_FILE, users)

def load_actual():
    return load_json(ACTUAL_FILE, [])

def save_actual(data):
    save_json(ACTUAL_FILE, data)

def load_supports():
    return load_json(SUPPORT_FILE, [])

def save_supports(data):
    save_json(SUPPORT_FILE, data)

def load_orders():
    return load_json(SELL_ORDERS_FILE, [])

def save_orders(data):
    save_json(SELL_ORDERS_FILE, data)

def load_banned():
    return load_json(BANNED_FILE, [])

def save_banned(data):
    save_json(BANNED_FILE, data)

async def register_user(user):
    users = load_users()
    user_ids = [u["id"] for u in users]
    if user.id not in user_ids:
        users.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "joined": datetime.now().isoformat()
        })
        save_users(users)

def get_user_by_id(user_id):
    users = load_users()
    for user in users:
        if user["id"] == user_id:
            return user
    return None

def get_user_by_username(username):
    users = load_users()
    for user in users:
        if user.get("username") == username:
            return user
    return None

def delete_old_requests(days=30):
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    
    orders = load_orders()
    new_orders = [o for o in orders if o.get("created_at", "") >= cutoff]
    save_orders(new_orders)
    
    supports = load_supports()
    new_supports = [s for s in supports if s.get("created_at", "") >= cutoff]
    save_supports(new_supports)
