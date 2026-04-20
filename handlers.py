import json
import os
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

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

# ========== КЛАВИАТУРЫ ==========
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="📝 Отзыв")],
            [KeyboardButton(text="🆘 Поддержка")],
            [KeyboardButton(text="ℹ️ Инфо")]
        ],
        resize_keyboard=True
    )

def profile_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Вывести")],
            [KeyboardButton(text="📋 Мои заявки")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Бан/Разбан")],
            [KeyboardButton(text="📋 Заявки")],
            [KeyboardButton(text="💰 Баланс")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def balance_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Начислить")],
            [KeyboardButton(text="➖ Списать")],
            [KeyboardButton(text="🔄 Обнулить")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def ban_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔨 Забанить")],
            [KeyboardButton(text="🔓 Разбанить")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ Назад")]],
        resize_keyboard=True
    )

def withdraw_method_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Карта", callback_data="method_card")],
            [InlineKeyboardButton(text="🤖 Crypto Bot", callback_data="method_crypto")]
        ]
    )

def withdraw_card_type_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 СБП", callback_data="card_sbp")],
            [InlineKeyboardButton(text="💳 Номер карты", callback_data="card_number")]
        ]
    )

def rating_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ 1", callback_data="rate_1"),
             InlineKeyboardButton(text="⭐⭐ 2", callback_data="rate_2"),
             InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data="rate_3")],
            [InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data="rate_4"),
             InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data="rate_5")]
        ]
    )

def review_skip_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Написать", callback_data="review_write")],
            [InlineKeyboardButton(text="⏩ Пропустить", callback_data="review_skip")]
        ]
    )

def review_anonymous_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Отправить с именем", callback_data="review_named")],
            [InlineKeyboardButton(text="👤 Отправить анонимно", callback_data="review_anonymous")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="review_cancel")]
        ]
    )

def withdraw_action_keyboard(wid):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{wid}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{wid}")],
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{wid}")]
        ]
    )

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

class AdminBanState(StatesGroup):
    username = State()

class AdminReplyState(StatesGroup):
    user_id = State()

# ========== ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ ==========
@router.message(Command("start"))
async def start_cmd(message: types.Message):
    register_user(message.from_user.id, message.from_user.username)
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы забанены")
        return
    await message.answer(
        "🔥 **Добро пожаловать!**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@router.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет доступа")
        return
    await message.answer("👑 **Админ-панель**", reply_markup=admin_keyboard(), parse_mode="Markdown")

@router.message(F.text == "◀️ Назад")
async def back_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("◀️ Главное меню", reply_markup=main_keyboard())

# ========== ПРОФИЛЬ ==========
@router.message(F.text == "👤 Профиль")
async def profile_cmd(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы забанены")
        return
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка, попробуйте /start")
        return
    
    active_count = get_active_requests_count(message.from_user.id)
    text = (
        f"👤 **Ваш профиль**\n\n"
        f"💰 **Баланс:** {user['balance']} USDT\n"
        f"📋 **Активных заявок:** {active_count}\n"
        f"📤 **Выведено всего:** {user['total_withdrawn']} USDT"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

# ========== ВЫВОД ==========
@router.message(F.text == "💰 Вывести")
async def withdraw_start_cmd(message: types.Message, state: FSMContext):
    if is_banned(message.from_user.id):
        return
    user = get_user(message.from_user.id)
    if user["balance"] < MIN_WITHDRAW:
        await message.answer(f"❌ Минимальная сумма вывода — **{MIN_WITHDRAW} USDT**", parse_mode="Markdown")
        return
    
    await message.answer(
        f"💸 **Введите сумму вывода (от {MIN_WITHDRAW} USDT):**",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(WithdrawState.amount)

@router.message(WithdrawState.amount)
async def withdraw_amount_cmd(message: types.Message, state: FSMContext):
    if message.text == "◀️ Назад":
        await state.clear()
        await profile_cmd(message)
        return
    
    try:
        amount = float(message.text)
        if amount < MIN_WITHDRAW:
            await message.answer(f"❌ Сумма должна быть **не менее {MIN_WITHDRAW} USDT**\nВведите другую сумму:", parse_mode="Markdown")
            return
        
        user = get_user(message.from_user.id)
        if amount > user["balance"]:
            await message.answer(f"❌ У вас {user['balance']} USDT\nВведите сумму не больше баланса:", parse_mode="Markdown")
            return
        
        await state.update_data(amount=amount)
        await message.answer("💳 **Выберите способ вывода:**", reply_markup=withdraw_method_keyboard())
    except:
        await message.answer("❌ Введите число")

@router.callback_query(lambda c: c.data == "method_card")
async def withdraw_method_card_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(method="card")
    await callback.message.edit_text("💳 **Выберите тип перевода:**", reply_markup=withdraw_card_type_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data == "method_crypto")
async def withdraw_method_crypto_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(method="crypto")
    await callback.message.edit_text(
        "🤖 **Отправьте ссылку на счёт из @CryptoBot**\n\n"
        "1. Перейдите в @CryptoBot\n"
        "2. Создайте счёт на оплату\n"
        "3. Пришлите ссылку сюда:",
        parse_mode="Markdown"
    )
    await state.set_state(WithdrawState.crypto_link)
    await callback.answer()

@router.callback_query(lambda c: c.data == "card_sbp")
async def withdraw_card_sbp_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(card_type="sbp")
    await callback.message.edit_text("📱 **Введите номер телефона (привязанный к банку):**")
    await state.set_state(WithdrawState.phone)
    await callback.answer()

@router.callback_query(lambda c: c.data == "card_number")
async def withdraw_card_number_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(card_type="card_number")
    await callback.message.edit_text("💳 **Введите номер карты (16 цифр):**")
    await state.set_state(WithdrawState.phone)
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
    
    await notify_admins(
        message.bot,
        f"💰 **Новая заявка на вывод!**\n\n"
        f"👤 От: @{message.from_user.username}\n"
        f"💵 Сумма: {amount} USDT\n"
        f"💳 Способ: {method}\n"
        f"📝 Реквизиты:\n{details}",
        withdraw_action_keyboard(withdraw["id"])
    )
    
    await message.answer(
        f"✅ **Заявка на вывод {amount} USDT отправлена!**\n\n"
        f"⏳ Статус: **В ожидании**\n"
        f"Администратор рассмотрит её в ближайшее время.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    
    await state.clear()

# ========== МОИ ЗАЯВКИ ==========
@router.message(F.text == "📋 Мои заявки")
async def my_withdraws_cmd(message: types.Message):
    if is_banned(message.from_user.id):
        return
    withdraws = get_user_withdraws(message.from_user.id)
    if not withdraws:
        await message.answer("📭 **У вас нет заявок на вывод**", parse_mode="Markdown", reply_markup=profile_keyboard())
        return
    
    withdraws.reverse()
    text = "📋 **Ваши заявки на вывод:**\n\n"
    status_map = {"pending": "⏳ В ожидании", "approved": "✅ Одобрено", "rejected": "❌ Отклонено"}
    
    for w in withdraws[:10]:
        text += f"• {w['amount']} USDT - {status_map.get(w['status'], '⏳ В ожидании')} - {w['created_at'][:10]}\n"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

# ========== ОТЗЫВ ==========
@router.message(F.text == "📝 Отзыв")
async def review_start_cmd(message: types.Message, state: FSMContext):
    if is_banned(message.from_user.id):
        return
    await message.answer("⭐ **Оцените наш сервис:**", reply_markup=rating_keyboard())
    await state.set_state(ReviewState.rating)

@router.callback_query(lambda c: c.data.startswith("rate_"))
async def review_rating_callback(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    await callback.message.edit_text("💬 **Напишите комментарий или пропустите:**", reply_markup=review_skip_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data == "review_write")
async def review_write_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ **Напишите ваш комментарий:**")
    await state.set_state(ReviewState.comment)
    await callback.answer()

@router.callback_query(lambda c: c.data == "review_skip")
async def review_skip_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await callback.message.edit_text("📢 **Как отправить отзыв?**", reply_markup=review_anonymous_keyboard())
    await callback.answer()

@router.message(ReviewState.comment)
async def review_comment_cmd(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("📢 **Как отправить отзыв?**", reply_markup=review_anonymous_keyboard())

@router.callback_query(lambda c: c.data.startswith("review_"))
async def review_send_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "review_cancel":
        await state.clear()
        await callback.message.edit_text("❌ Отзыв отменён", reply_markup=main_keyboard())
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
    await callback.message.edit_text("✅ **Спасибо за ваш отзыв!**", reply_markup=main_keyboard())
    await callback.answer()

# ========== ПОДДЕРЖКА ==========
@router.message(F.text == "🆘 Поддержка")
async def support_cmd(message: types.Message):
    if is_banned(message.from_user.id):
        return
    await message.answer(
        "📞 **Связь с администратором**\n\nНапишите ваш вопрос, и мы ответим вам в ближайшее время.",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )

@router.message(F.text == "ℹ️ Инфо")
async def info_cmd(message: types.Message):
    text = (
        "ℹ️ **Информация**\n\n"
        "🕒 **График работы:**\nПн-Пт с 11:00 до 19:30\n\n"
        "💸 **Вывод средств:**\nПроизводится с 11:00 до 19:30\n\n"
        f"💰 **Минимальная сумма вывода:** {MIN_WITHDRAW} USDT\n\n"
        "⭐ **Наши отзывы:**\nhttps://t.me/otzyvOPK\n\n"
        "📢 **Подробная информация:**\n👉 https://t.me/+ZAJelSN78aliNzIx\n\n"
        "📞 **По всем вопросам:** обратитесь в поддержку"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard())

# ========== ОБРАБОТКА ТЕКСТА В ПОДДЕРЖКУ ==========
@router.message(F.text)
async def support_message_cmd(message: types.Message):
    if is_banned(message.from_user.id):
        return
    if message.from_user.id in ADMIN_IDS:
        return
    if message.text in ["👤 Профиль", "📝 Отзыв", "🆘 Поддержка", "ℹ️ Инфо", "◀️ Назад", "💰 Вывести", "📋 Мои заявки"]:
        return
    
    await notify_admins(
        message.bot,
        f"🆘 **Вопрос от пользователя!**\n\n👤 От: @{message.from_user.username}\n📝 Сообщение: {message.text}"
    )
    await message.answer(
        "✅ **Сообщение отправлено!**\nАдминистратор ответит вам в ближайшее время.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

# ========== АДМИН-ПАНЕЛЬ ==========
@router.message(F.text == "👥 Бан/Разбан")
async def ban_menu_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("👥 **Управление баном**", reply_markup=ban_keyboard(), parse_mode="Markdown")

@router.message(F.text == "🔨 Забанить")
async def ban_user_start_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Введите **username** пользователя (без @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBanState.username)

@router.message(AdminBanState.username)
async def ban_user_execute_cmd(message: types.Message, state: FSMContext):
    if message.text == "◀️ Назад":
        await state.clear()
        await ban_menu_cmd(message)
        return
    
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    ban_user(user["id"])
    await message.answer(f"✅ **Пользователь @{user['username']} забанен**", parse_mode="Markdown", reply_markup=admin_keyboard())
    await notify_admins(message.bot, f"🔨 Админ забанил @{user['username']}")
    await notify_user(message.bot, user["id"], "❌ **Вы были забанены администратором.**")
    await state.clear()

@router.message(F.text == "🔓 Разбанить")
async def unban_user_start_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Введите **username** пользователя (без @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBanState.username)

@router.message(AdminBanState.username)
async def unban_user_execute_cmd(message: types.Message, state: FSMContext):
    if message.text == "◀️ Назад":
        await state.clear()
        await ban_menu_cmd(message)
        return
    
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    unban_user(user["id"])
    await message.answer(f"✅ **Пользователь @{user['username']} разбанен**", parse_mode="Markdown", reply_markup=admin_keyboard())
    await notify_admins(message.bot, f"🔓 Админ разбанил @{user['username']}")
    await notify_user(message.bot, user["id"], "✅ **Вы были разбанены.**")
    await state.clear()

@router.message(F.text == "📋 Заявки")
async def list_withdraws_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    withdraws = load_withdraws()
    pending = [w for w in withdraws if w["status"] == "pending"]
    
    if not pending:
        await message.answer("📭 **Нет активных заявок**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    for w in pending:
        text = (
            f"💰 **Заявка на вывод**\n\n"
            f"👤 От: @{w['username']}\n"
            f"💵 Сумма: {w['amount']} USDT\n"
            f"💳 Способ: {w['method']}\n"
            f"📝 Реквизиты:\n{w['details']}\n"
            f"📅 {w['created_at'][:19]}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=withdraw_action_keyboard(w["id"]))

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
            await state.update_data(user_id=w["user_id"])
            await callback.message.answer("💬 **Введите ответ пользователю:**")
            await state.set_state(AdminReplyState.user_id)
            break
    
    await callback.answer()

@router.message(AdminReplyState.user_id)
async def send_reply_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    
    await notify_user(message.bot, user_id, f"💬 **Ответ администратора:**\n\n{message.text}")
    await message.answer("✅ **Ответ отправлен!**", reply_markup=admin_keyboard())
    await state.clear()

@router.message(F.text == "💰 Баланс")
async def balance_admin_menu_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("💰 **Управление балансом**", reply_markup=balance_admin_keyboard(), parse_mode="Markdown")

@router.message(F.text == "➕ Начислить")
async def add_balance_start_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(action="add")
    await message.answer("Введите **username** пользователя (без @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBalanceState.username)

@router.message(F.text == "➖ Списать")
async def subtract_balance_start_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(action="subtract")
    await message.answer("Введите **username** пользователя (без @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBalanceState.username)

@router.message(F.text == "🔄 Обнулить")
async def reset_balance_start_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(action="reset")
    await message.answer("Введите **username** пользователя (без @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBalanceState.username)

@router.message(AdminBalanceState.username)
async def balance_get_user_cmd(message: types.Message, state: FSMContext):
    if message.text == "◀️ Назад":
        await state.clear()
        await balance_admin_menu_cmd(message)
        return
    
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    await state.update_data(username=message.text, user_id=user["id"])
    data = await state.get_data()
    action = data.get("action")
    
    if action == "reset":
        old_balance = user["balance"]
        update_balance(user["id"], 0)
        await message.answer(f"✅ **Баланс обнулён**\n\n👤 @{user['username']}\n📊 {old_balance} → 0 USDT", parse_mode="Markdown", reply_markup=admin_keyboard())
        await notify_admins(message.bot, f"🔄 Админ обнулил баланс @{user['username']} ({old_balance} → 0 USDT)")
        await notify_user(message.bot, user["id"], f"🔄 **Ваш баланс обнулён!**\nБыло: {old_balance} USDT\nСтало: 0 USDT")
        await state.clear()
    else:
        action_text = "начислить" if action == "add" else "списать"
        await message.answer(f"👤 @{user['username']}\n💰 Баланс: {user['balance']} USDT\n\n💵 Введите сумму для **{action_text}** (USDT):", parse_mode="Markdown")
        await state.set_state(AdminBalanceState.amount)

@router.message(AdminBalanceState.amount)
async def balance_amount_cmd(message: types.Message, state: FSMContext):
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
            await message.answer(f"✅ **Начислено {amount} USDT**\n\n👤 @{username}\n📊 {user['balance'] - amount} → {new_balance} USDT", parse_mode="Markdown", reply_markup=admin_keyboard())
            await notify_admins(message.bot, f"➕ Админ начислил {amount} USDT @{username}")
            await notify_user(message.bot, user_id, f"➕ **Начислено {amount} USDT!**\n💰 Новый баланс: {new_balance} USDT")
        else:
            if amount > user["balance"]:
                await message.answer(f"❌ Недостаточно средств! Баланс: {user['balance']} USDT")
                return
            new_balance = user["balance"] - amount
            update_balance(user_id, new_balance)
            await message.answer(f"✅ **Списано {amount} USDT**\n\n👤 @{username}\n📊 {user['balance'] + amount} → {new_balance} USDT", parse_mode="Markdown", reply_markup=admin_keyboard())
            await notify_admins(message.bot, f"➖ Админ списал {amount} USDT у @{username}")
            await notify_user(message.bot, user_id, f"➖ **Списано {amount} USDT**\n💰 Новый баланс: {new_balance} USDT")
        
        await state.clear()
    except:
        await message.answer("❌ Введите число")
