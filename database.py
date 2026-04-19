import json
import os
from datetime import datetime, timedelta

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

# ========== USERS ==========
def load_users():
    return load_json(USERS_FILE, [])

def save_users(users):
    save_json(USERS_FILE, users)

def get_user_by_id(user_id):
    for u in load_users():
        if u["id"] == user_id:
            return u
    return None

def get_user_by_username(username):
    username = username.lower().replace("@", "")
    for u in load_users():
        if u.get("username") and u["username"].lower() == username:
            return u
    return None

def update_user(user_id, data):
    users = load_users()
    for i, u in enumerate(users):
        if u["id"] == user_id:
            users[i].update(data)
            save_users(users)
            return True
    return False

def register_user(user):
    users = load_users()
    for u in users:
        if u["id"] == user.id:
            return False
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
    return True

def get_rating_list():
    users = load_users()
    rated = [u for u in users if u.get("rating", 0) > 0]
    rated.sort(key=lambda x: x.get("rating", 0))
    return rated

# ========== BANNED ==========
def load_banned():
    return load_json(BANNED_FILE, [])

def save_banned(banned):
    save_json(BANNED_FILE, banned)

def is_banned(user_id):
    return user_id in load_banned()

def ban_user(user_id):
    banned = load_banned()
    if user_id not in banned:
        banned.append(user_id)
        save_banned(banned)
        return True
    return False

def unban_user(user_id):
    banned = load_banned()
    if user_id in banned:
        banned.remove(user_id)
        save_banned(banned)
        return True
    return False

# ========== WITHDRAWS ==========
def load_withdraws():
    return load_json(WITHDRAW_FILE, [])

def save_withdraws(withdraws):
    save_json(WITHDRAW_FILE, withdraws)

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

def delete_old_withdraws(days=1):
    """Удаляет заявки со статусом approved/rejected старше days дней"""
    cutoff = datetime.now() - timedelta(days=days)
    withdraws = load_withdraws()
    new_withdraws = []
    for w in withdraws:
        if w["status"] == "pending":
            new_withdraws.append(w)
        else:
            created = datetime.fromisoformat(w["created_at"])
            if created > cutoff:
                new_withdraws.append(w)
    save_withdraws(new_withdraws)
    return len(withdraws) - len(new_withdraws)

# ========== REVIEWS ==========
def load_reviews():
    return load_json(REVIEWS_FILE, [])

def save_reviews(reviews):
    save_json(REVIEWS_FILE, reviews)

def add_review(review):
    reviews = load_reviews()
    reviews.append(review)
    save_reviews(reviews)
