import json
import os
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_IDS, REVIEWS_CHANNEL, MIN_WITHDRAW

router = Router()

# ========== ДАННЫЕ ==========
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

# ========== УВЕДОМЛЕНИЯ ==========
async def notify_admins(bot, text, reply_markup=None):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown", reply_markup=reply_markup)
        except:
            pass

async def notify_user(bot, user_id, text):
    try:
        await bot.send_message(user_id, text, parse_mode="Markdown")
    except:
        pass

# ========== СОСТОЯНИЯ ==========
class WithdrawState(StatesGroup):
    amount = State()
    card_type = State()
    phone = State()
    bank = State()
    name = State()
    crypto_link = State()

class ReviewState(StatesGroup):
    rating = State()
    comment = State()

class AdminBalanceState(StatesGroup):
    username = State()
    amount = State()
    action = State()

# ========== ГЛАВНОЕ МЕНЮ (ВСЕ КНОПКИ INLINE) ==========
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📝 Отзыв", callback_data="review")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")]
    ])

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    register_user(message.from_user.id, message.from_user.username)
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы забанены")
        return
    await message.answer(
        "🔥 **Добро пожаловать!**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ========== ПРОФИЛЬ ==========
@router.callback_query(lambda c: c.data == "profile")
async def profile_callback(callback: types.CallbackQuery):
    if is_banned(callback.from_user.id):
        await callback.answer("Вы забанены", show_alert=True)
        return
    
    user = get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("❌ Ошибка", reply_markup=main_menu())
        return
    
    active_count = get_active_requests_count(callback.from_user.id)
    text = (
        f"👤 **Ваш профиль**\n\n"
        f"💰 **Баланс:** {user['balance']} USDT\n"
        f"📋 **Активных заявок:** {active_count}\n"
        f"📤 **Выведено всего:** {user['total_withdrawn']} USDT"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Вывести", callback_data="withdraw_start")],
        [InlineKeyboardButton(text="📋 Мои заявки", callback_data="my_requests")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

# ========== МОИ ЗАЯВКИ ==========
@router.callback_query(lambda c: c.data == "my_requests")
async def my_requests_callback(callback: types.CallbackQuery):
    withdraws = get_user_withdraws(callback.from_user.id)
    if not withdraws:
        await callback.answer("У вас нет заявок", show_alert=True)
        return
    
    withdraws.reverse()
    text = "📋 **Ваши заявки на вывод:**\n\n"
    status_map = {"pending": "⏳ В ожидании", "approved": "✅ Одобрено", "rejected": "❌ Отклонено"}
    
    for w in withdraws[:10]:
        text += f"• {w['amount']} USDT - {status_map.get(w['status'], '⏳ В ожидании')} - {w['created_at'][:10]}\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

# ========== ВЫВОД ==========
@router.callback_query(lambda c: c.data == "withdraw_start")
async def withdraw_start_callback(callback: types.CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if user["balance"] < MIN_WITHDRAW:
        await callback.answer(f"Минимальная сумма {MIN_WITHDRAW} USDT", show_alert=True)
        return
    
    await state.set_state(WithdrawState.amount)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="profile")]
    ])
    await callback.message.edit_text(
        f"💸 **Введите сумму вывода (от {MIN_WITHDRAW} USDT):**",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await callback.answer()

@router.message(WithdrawState.amount)
async def withdraw_amount_cmd(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < MIN_WITHDRAW:
            await message.answer(f"❌ Сумма должна быть не менее {MIN_WITHDRAW} USDT\nВведите другую сумму:")
            return
        
        user = get_user(message.from_user.id)
        if amount > user["balance"]:
            await message.answer(f"❌ У вас {user['balance']} USDT\nВведите сумму не больше баланса:")
            return
        
        await state.update_data(amount=amount)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Карта", callback_data="method_card")],
            [InlineKeyboardButton(text="🤖 Crypto Bot", callback_data="method_crypto")],
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="profile")]
        ])
        await message.answer("💳 **Выберите способ вывода:**", reply_markup=kb, parse_mode="Markdown")
    except:
        await message.answer("❌ Введите число")

@router.callback_query(lambda c: c.data == "method_card")
async def withdraw_card_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(method="card")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 СБП", callback_data="card_sbp")],
        [InlineKeyboardButton(text="💳 Номер карты", callback_data="card_number")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="withdraw_start")]
    ])
    await callback.message.edit_text("💳 **Выберите тип перевода:**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data == "method_crypto")
async def withdraw_crypto_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(method="crypto")
    await state.set_state(WithdrawState.crypto_link)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="profile")]
    ])
    await callback.message.edit_text(
        "🤖 **Отправьте ссылку на счёт из @CryptoBot**\n\n"
        "1. Перейдите в @CryptoBot\n"
        "2. Создайте счёт на оплату\n"
        "3. Пришлите ссылку сюда:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "card_sbp")
async def card_sbp_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(card_type="sbp")
    await state.set_state(WithdrawState.phone)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="profile")]
    ])
    await callback.message.edit_text("📱 **Введите номер телефона (привязанный к банку):**", reply_markup=kb)
    await callback.answer()

@router.callback_query(lambda c: c.data == "card_number")
async def card_number_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(card_type="card_number")
    await state.set_state(WithdrawState.phone)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="profile")]
    ])
    await callback.message.edit_text("💳 **Введите номер карты (16 цифр):**", reply_markup=kb)
    await callback.answer()

@router.message(WithdrawState.phone)
async def withdraw_phone_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get("card_type") == "sbp":
        await state.update_data(phone=message.text)
        await message.answer("🏦 **Введите название вашего банка:**")
        await state.set_state(WithdrawState.bank)
    else:
        await state.update_data(card_number=message.text)
        await message.answer("👤 **Введите имя получателя (как на карте):**")
        await state.set_state(WithdrawState.name)

@router.message(WithdrawState.bank)
async def withdraw_bank_cmd(message: types.Message, state: FSMContext):
    await state.update_data(bank=message.text)
    await message.answer("👤 **Введите имя получателя:**")
    await state.set_state(WithdrawState.name)

@router.message(WithdrawState.name)
async def withdraw_name_cmd(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await finish_withdraw(message, state)

@router.message(WithdrawState.crypto_link)
async def withdraw_crypto_link_cmd(message: types.Message, state: FSMContext):
    await state.update_data(crypto_link=message.text)
    await finish_withdraw(message, state)

async def finish_withdraw(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data["amount"]
    method = data["method"]
    
    if method == "card":
        if data.get("card_type") == "sbp":
            details = f"СБП\nТелефон: {data['phone']}\nБанк: {data['bank']}\nИмя: {data['name']}"
        else:
            details = f"Номер карты: {data['card_number']}\nИмя: {data['name']}"
    else:
        details = f"Crypto Bot ссылка: {data['crypto_link']}"
    
    withdraw = {
        "id": int(datetime.now().timestamp()),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "amount": amount,
        "method": method,
        "details": details,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    add_withdraw(withdraw)
    
    # Кнопки для админов
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{withdraw['id']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{withdraw['id']}")],
        [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{withdraw['id']}")]
    ])
    
    await notify_admins(
        message.bot,
        f"💰 **Новая заявка на вывод!**\n\n"
        f"👤 От: @{message.from_user.username}\n"
        f"💵 Сумма: {amount} USDT\n"
        f"💳 Способ: {method}\n"
        f"📝 Реквизиты:\n{details}",
        admin_kb
    )
    
    await message.answer(
        f"✅ **Заявка на вывод {amount} USDT отправлена!**\n\n⏳ Статус: **В ожидании**",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await state.clear()

# ========== ОТЗЫВ ==========
@router.callback_query(lambda c: c.data == "review")
async def review_start_callback(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 1", callback_data="rate_1"),
         InlineKeyboardButton(text="⭐⭐ 2", callback_data="rate_2"),
         InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data="rate_3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data="rate_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data="rate_5")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("⭐ **Оцените наш сервис:**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("rate_"))
async def review_rating_callback(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Написать", callback_data="review_write")],
        [InlineKeyboardButton(text="⏩ Пропустить", callback_data="review_skip")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="review")]
    ])
    await callback.message.edit_text("💬 **Напишите комментарий или пропустите:**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data == "review_write")
async def review_write_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ReviewState.comment)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="review")]
    ])
    await callback.message.edit_text("✏️ **Напишите ваш комментарий:**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data == "review_skip")
async def review_skip_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await show_anonymous_options(callback.message, state)

async def show_anonymous_options(message: types.Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Отправить с именем", callback_data="review_named")],
        [InlineKeyboardButton(text="👤 Отправить анонимно", callback_data="review_anonymous")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="review")]
    ])
    await message.edit_text("📢 **Как отправить отзыв?**", reply_markup=kb, parse_mode="Markdown")

@router.message(ReviewState.comment)
async def review_comment_cmd(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await show_anonymous_options(message, state)

@router.callback_query(lambda c: c.data.startswith("review_"))
async def review_send_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "review_cancel":
        await callback.message.edit_text("❌ Отзыв отменён", reply_markup=main_menu())
        await callback.answer()
        return
    
    data = await state.get_data()
    rating = data.get("rating")
    comment = data.get("comment")
    is_anonymous = callback.data == "review_anonymous"
    
    review = {
        "id": int(datetime.now().timestamp()),
        "user_id": None if is_anonymous else callback.from_user.id,
        "username": None if is_anonymous else callback.from_user.username,
        "rating": rating,
        "comment": comment,
        "is_anonymous": is_anonymous,
        "created_at": datetime.now().isoformat()
    }
    add_review(review)
    
    stars = "⭐" * rating
    name = "Аноним" if is_anonymous else f"@{callback.from_user.username}"
    comment_text = comment or "Без комментария"
    
    try:
        await callback.bot.send_message(
            REVIEWS_CHANNEL,
            f"⭐ **Новый отзыв!**\n\n👤 {name}\n⭐ {rating}/5 {stars}\n💬 {comment_text}\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await notify_admins(callback.bot, f"⭐ **Новый отзыв!**\n\n👤 {name}\n⭐ {rating}/5\n💬 {comment_text}")
    await state.clear()
    await callback.message.edit_text("✅ **Спасибо за ваш отзыв!**", reply_markup=main_menu())
    await callback.answer()

# ========== ПОДДЕРЖКА ==========
@router.callback_query(lambda c: c.data == "support")
async def support_callback(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(
        "📞 **Связь с администратором**\n\nНапишите ваш вопрос, и мы ответим вам.",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await callback.answer()

# ========== ИНФО ==========
@router.callback_query(lambda c: c.data == "info")
async def info_callback(callback: types.CallbackQuery):
    text = (
        "ℹ️ **Информация**\n\n"
        "🕒 **График работы:**\nПн-Пт с 11:00 до 19:30\n\n"
        "💸 **Вывод средств:**\nПроизводится с 11:00 до 19:30\n\n"
        f"💰 **Минимальная сумма вывода:** {MIN_WITHDRAW} USDT\n\n"
        "⭐ **Наши отзывы:**\nhttps://t.me/otzyvOPK\n\n"
        "📢 **Подробная информация:**\n👉 https://t.me/+ZAJelSN78aliNzIx\n\n"
        "📞 **По всем вопросам:** обратитесь в поддержку"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

# ========== НАЗАД В ГЛАВНОЕ МЕНЮ ==========
@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔥 **Добро пожаловать!**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await callback.answer()

# ========== ОБРАБОТКА ТЕКСТА В ПОДДЕРЖКУ ==========
@router.message(F.text)
async def support_message_cmd(message: types.Message):
    if is_banned(message.from_user.id):
        return
    if message.from_user.id in ADMIN_IDS:
        return
    
    await notify_admins(
        message.bot,
        f"🆘 **Вопрос от пользователя!**\n\n👤 От: @{message.from_user.username}\n📝 Сообщение: {message.text}"
    )
    await message.answer(
        "✅ **Сообщение отправлено!**\nАдминистратор ответит вам.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ========== АДМИН-ПАНЕЛЬ ==========
@router.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет доступа")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Бан/Разбан", callback_data="admin_ban")],
        [InlineKeyboardButton(text="📋 Заявки", callback_data="admin_requests")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="admin_balance")],
        [InlineKeyboardButton(text="◀️ Выход", callback_data="back_to_main")]
    ])
    await message.answer("👑 **Админ-панель**", reply_markup=kb, parse_mode="Markdown")

@router.callback_query(lambda c: c.data == "admin_ban")
async def admin_ban_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔨 Забанить", callback_data="ban_user_start")],
        [InlineKeyboardButton(text="🔓 Разбанить", callback_data="unban_user_start")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text("👥 **Управление баном**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_requests")
async def admin_requests_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    withdraws = load_withdraws()
    pending = [w for w in withdraws if w["status"] == "pending"]
    
    if not pending:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ])
        await callback.message.edit_text("📭 **Нет активных заявок**", reply_markup=kb, parse_mode="Markdown")
        await callback.answer()
        return
    
    for w in pending:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{w['id']}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{w['id']}")],
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{w['id']}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ])
        text = (
            f"💰 **Заявка на вывод**\n\n"
            f"👤 От: @{w['username']}\n"
            f"💵 Сумма: {w['amount']} USDT\n"
            f"💳 Способ: {w['method']}\n"
            f"📝 Реквизиты:\n{w['details']}\n"
            f"📅 {w['created_at'][:19]}"
        )
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    
    await callback.message.delete()
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_balance")
async def admin_balance_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Начислить", callback_data="balance_add")],
        [InlineKeyboardButton(text="➖ Списать", callback_data="balance_subtract")],
        [InlineKeyboardButton(text="🔄 Обнулить", callback_data="balance_reset")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text("💰 **Управление балансом**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_back")
async def admin_back_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Бан/Разбан", callback_data="admin_ban")],
        [InlineKeyboardButton(text="📋 Заявки", callback_data="admin_requests")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="admin_balance")],
        [InlineKeyboardButton(text="◀️ Выход", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("👑 **Админ-панель**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# ========== БАН/РАЗБАН (ВВОД USERNAME) ==========
@router.callback_query(lambda c: c.data == "ban_user_start")
async def ban_user_start_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    await state.update_data(action="ban")
    await state.set_state(AdminBalanceState.username)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_ban")]
    ])
    await callback.message.edit_text("🔨 **Введите username пользователя (без @):**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data == "unban_user_start")
async def unban_user_start_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    await state.update_data(action="unban")
    await state.set_state(AdminBalanceState.username)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_ban")]
    ])
    await callback.message.edit_text("🔓 **Введите username пользователя (без @):**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# ========== БАЛАНС (ВВОД USERNAME) ==========
@router.callback_query(lambda c: c.data == "balance_add")
async def balance_add_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    await state.update_data(action="add")
    await state.set_state(AdminBalanceState.username)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_balance")]
    ])
    await callback.message.edit_text("➕ **Введите username пользователя (без @):**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data == "balance_subtract")
async def balance_subtract_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    await state.update_data(action="subtract")
    await state.set_state(AdminBalanceState.username)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_balance")]
    ])
    await callback.message.edit_text("➖ **Введите username пользователя (без @):**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data == "balance_reset")
async def balance_reset_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    await state.update_data(action="reset")
    await state.set_state(AdminBalanceState.username)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_balance")]
    ])
    await callback.message.edit_text("🔄 **Введите username пользователя (без @):**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# ========== ОБРАБОТКА USERNAME ==========
@router.message(AdminBalanceState.username)
async def admin_username_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("action")
    username = message.text.strip().replace("@", "")
    
    user = get_user_by_username(username)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    if action == "ban":
        ban_user(user["id"])
        await message.answer(f"✅ **Пользователь @{user['username']} забанен**", parse_mode="Markdown")
        await notify_admins(message.bot, f"🔨 Админ забанил @{user['username']}")
        await notify_user(message.bot, user["id"], "❌ **Вы были забанены администратором.**")
        await state.clear()
        await admin_cmd(message)
        
    elif action == "unban":
        unban_user(user["id"])
        await message.answer(f"✅ **Пользователь @{user['username']} разбанен**", parse_mode="Markdown")
        await notify_admins(message.bot, f"🔓 Админ разбанил @{user['username']}")
        await notify_user(message.bot, user["id"], "✅ **Вы были разбанены.**")
        await state.clear()
        await admin_cmd(message)
        
    elif action == "reset":
        old_balance = user["balance"]
        update_balance(user["id"], 0)
        await message.answer(f"✅ **Баланс обнулён**\n\n👤 @{user['username']}\n📊 {old_balance} → 0 USDT", parse_mode="Markdown")
        await notify_admins(message.bot, f"🔄 Админ обнулил баланс @{user['username']} ({old_balance} → 0 USDT)")
        await notify_user(message.bot, user["id"], f"🔄 **Ваш баланс обнулён!**\nБыло: {old_balance} USDT\nСтало: 0 USDT")
        await state.clear()
        await admin_cmd(message)
        
    elif action in ["add", "subtract"]:
        await state.update_data(user_id=user["id"], username=user["username"])
        action_text = "начислить" if action == "add" else "списать"
        await message.answer(f"👤 @{user['username']}\n💰 Баланс: {user['balance']} USDT\n\n💵 **Введите сумму для {action_text} (USDT):**", parse_mode="Markdown")
        await state.set_state(AdminBalanceState.amount)

# ========== ОБРАБОТКА СУММЫ ==========
@router.message(AdminBalanceState.amount)
async def admin_amount_cmd(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0")
            return
        
        data = await state.get_data()
        user_id = data.get("user_id")
        username = data.get("username")
        action = data.get("action")
        user = get_user(user_id)
        
        if action == "add":
            new_balance = user["balance"] + amount
            update_balance(user_id, new_balance)
            await message.answer(f"✅ **Начислено {amount} USDT**\n\n👤 @{username}\n📊 {user['balance'] - amount} → {new_balance} USDT", parse_mode="Markdown")
            await notify_admins(message.bot, f"➕ Админ начислил {amount} USDT @{username}")
            await notify_user(message.bot, user_id, f"➕ **Начислено {amount} USDT!**\n💰 Новый баланс: {new_balance} USDT")
        else:
            if amount > user["balance"]:
                await message.answer(f"❌ Недостаточно средств! Баланс: {user['balance']} USDT")
                return
            new_balance = user["balance"] - amount
            update_balance(user_id, new_balance)
            await message.answer(f"✅ **Списано {amount} USDT**\n\n👤 @{username}\n📊 {user['balance'] + amount} → {new_balance} USDT", parse_mode="Markdown")
            await notify_admins(message.bot, f"➖ Админ списал {amount} USDT у @{username}")
            await notify_user(message.bot, user_id, f"➖ **Списано {amount} USDT**\n💰 Новый баланс: {new_balance} USDT")
        
        await state.clear()
        await admin_cmd(message)
    except:
        await message.answer("❌ Введите число")

# ========== ОБРАБОТКА ЗАЯВОК (APPROVE/REJECT/REPLY) ==========
@router.callback_query(lambda c: c.data.startswith("approve_"))
async def approve_withdraw_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    wid = int(callback.data.split("_")[1])
    w = update_withdraw_status(wid, "approved")
    
    if w:
        user = get_user(w["user_id"])
        if user:
            new_balance = user["balance"] - w["amount"]
            update_balance(w["user_id"], new_balance)
            add_to_withdrawn(w["user_id"], w["amount"])
            await notify_user(callback.bot, w["user_id"], f"✅ **Заявка одобрена!**\n💵 {w['amount']} USDT\n💰 Новый баланс: {new_balance} USDT")
        
        await notify_admins(callback.bot, f"✅ Админ одобрил заявку @{w['username']} на {w['amount']} USDT")
        await callback.message.edit_text(f"✅ Одобрено\n{callback.message.text}")
    
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("reject_"))
async def reject_withdraw_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    wid = int(callback.data.split("_")[1])
    w = update_withdraw_status(wid, "rejected")
    
    if w:
        await notify_user(callback.bot, w["user_id"], f"❌ **Заявка отклонена!**\n💵 {w['amount']} USDT\n📞 Обратитесь в поддержку")
        await notify_admins(callback.bot, f"❌ Админ отклонил заявку @{w['username']} на {w['amount']} USDT")
        await callback.message.edit_text(f"❌ Отклонено\n{callback.message.text}")
    
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("reply_"))
async def reply_to_withdraw_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    wid = int(callback.data.split("_")[1])
    withdraws = load_withdraws()
    for w in withdraws:
        if w["id"] == wid:
            await state.update_data(reply_user_id=w["user_id"])
            await state.set_state(AdminBalanceState.username)  # переиспользуем состояние
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_requests")]
            ])
            await callback.message.answer("💬 **Введите ответ пользователю:**", reply_markup=kb)
            break
    
    await callback.answer()

@router.message(AdminBalanceState.username)
async def send_reply_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_user_id")
    
    if user_id:
        await notify_user(message.bot, user_id, f"💬 **Ответ администратора:**\n\n{message.text}")
        await message.answer("✅ **Ответ отправлен!**")
    
    await state.clear()
    await admin_cmd(message)
