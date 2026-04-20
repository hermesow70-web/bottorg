import json
import os
from datetime import datetime

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

USERS_FILE = f"{DATA_FOLDER}/users.json"
WITHDRAW_FILE = f"{DATA_FOLDER}/withdraws.json"
REVIEWS_FILE = f"{DATA_FOLDER}/reviews.json"

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_withdraws():
    try:
        with open(WITHDRAW_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_withdraws(withdraws):
    with open(WITHDRAW_FILE, "w", encoding="utf-8") as f:
        json.dump(withdraws, f, ensure_ascii=False, indent=2)

def load_reviews():
    try:
        with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_reviews(reviews):
    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

def register_user(user_id, username):
    users = load_users()
    for u in users:
        if u["id"] == user_id:
            return
    users.append({
        "id": user_id,
        "username": username,
        "balance": 0,
        "total_withdrawn": 0,
        "banned": False,
        "joined": datetime.now().isoformat()
    })
    save_users(users)

def get_user(user_id):
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

def update_balance(user_id, new_balance):
    users = load_users()
    for i, u in enumerate(users):
        if u["id"] == user_id:
            users[i]["balance"] = new_balance
            save_users(users)
            return True
    return False

def add_to_withdrawn(user_id, amount):
    users = load_users()
    for i, u in enumerate(users):
        if u["id"] == user_id:
            users[i]["total_withdrawn"] = u.get("total_withdrawn", 0) + amount
            save_users(users)
            return True
    return False

def is_banned(user_id):
    users = load_users()
    for u in users:
        if u["id"] == user_id:
            return u.get("banned", False)
    return False

def ban_user(user_id):
    users = load_users()
    for i, u in enumerate(users):
        if u["id"] == user_id:
            users[i]["banned"] = True
            save_users(users)
            return True
    return False

def unban_user(user_id):
    users = load_users()
    for i, u in enumerate(users):
        if u["id"] == user_id:
            users[i]["banned"] = False
            save_users(users)
            return True
    return False

def get_active_requests_count(user_id):
    withdraws = load_withdraws()
    count = 0
    for w in withdraws:
        if w["user_id"] == user_id and w["status"] == "pending":
            count += 1
    return count

def get_user_withdraws(user_id):
    withdraws = load_withdraws()
    return [w for w in withdraws if w["user_id"] == user_id]

def add_withdraw(withdraw):
    withdraws = load_withdraws()
    withdraws.append(withdraw)
    save_withdraws(withdraws)

def update_withdraw_status(wid, status):
    withdraws = load_withdraws()
    for w in withdraws:
        if w["id"] == wid:
            w["status"] = status
            save_withdraws(withdraws)
            return w
    return None

def add_review(review):
    reviews = load_reviews()
    reviews.append(review)
    save_reviews(reviews)
