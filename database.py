import json
import os
from datetime import datetime

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

USERS_FILE = f"{DATA_FOLDER}/users.json"
BANNED_FILE = f"{DATA_FOLDER}/banned.json"
WITHDRAW_FILE = f"{DATA_FOLDER}/withdraws.json"
REVIEWS_FILE = f"{DATA_FOLDER}/reviews.json"

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

def load_banned():
    return load_json(BANNED_FILE, [])

def save_banned(data):
    save_json(BANNED_FILE, data)

def load_withdraws():
    return load_json(WITHDRAW_FILE, [])

def save_withdraws(data):
    save_json(WITHDRAW_FILE, data)

def load_reviews():
    return load_json(REVIEWS_FILE, [])

def save_reviews(data):
    save_json(REVIEWS_FILE, data)

async def register_user(user):
    users = load_users()
    found = False
    for u in users:
        if u["id"] == user.id:
            found = True
            break
    
    if not found:
        users.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": 0,
            "total_withdrawn": 0,
            "rating": 0,
            "rating_score": 0,
            "rating_count": 0,
            "joined": datetime.now().isoformat()
        })
        save_users(users)

def get_user_by_id(user_id):
    users = load_users()
    for u in users:
        if u["id"] == user_id:
            return u
    return None

def get_user_by_username(username):
    users = load_users()
    username = username.lower().replace("@", "")
    for u in users:
        if u.get("username") and u["username"].lower() == username:
            return u
    return None

def update_user_by_id(user_id, data):
    users = load_users()
    for i, u in enumerate(users):
        if u["id"] == user_id:
            users[i].update(data)
            break
    save_users(users)

def update_user_by_username(username, data):
    users = load_users()
    username = username.lower().replace("@", "")
    for i, u in enumerate(users):
        if u.get("username") and u["username"].lower() == username:
            users[i].update(data)
            save_users(users)
            return users[i]
    return None

def get_rating_list():
    users = load_users()
    rated = [u for u in users if u.get("rating", 0) > 0]
    rated.sort(key=lambda x: x.get("rating", 0))
    return rated
