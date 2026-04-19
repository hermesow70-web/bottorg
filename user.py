from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    register_user, get_user, update_balance, add_to_withdrawn,
    get_active_requests_count, get_user_withdraws, add_withdraw,
    add_review, load_withdraws, is_banned
)
from keyboards import (
    main_keyboard, profile_keyboard, back_keyboard, cancel_keyboard,
    rating_keyboard, review_skip_keyboard, withdraw_action_keyboard
)
from config import ADMIN_IDS, REVIEWS_CHANNEL

user_router = Router()

class WithdrawState(StatesGroup):
    amount = State()
    method = State()
    card_type = State()
    phone = State()
    bank = State()
    name = State()
    crypto_link = State()

class ReviewState(StatesGroup):
    rating = State()
    comment = State()

# ========== УВЕДОМЛЕНИЯ ==========
async def notify_admins(bot, text):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown")
        except:
            pass

# ========== СТАРТ ==========
@user_router.message(Command("start"))
async def start(message: types.Message):
    register_user(message.from_user.id, message.from_user.username)
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы забанены")
        return
    await message.answer(
        "🔥 **Добро пожаловать!**\n\n"
        "Выберите действие:",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# ========== ПРОФИЛЬ ==========
@user_router.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
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

# ========== ГЛАВНОЕ МЕНЮ ==========
@user_router.message(F.text == "🔙 Главное меню")
@user_router.message(F.text == "🏠 Главное меню")
async def go_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 **Главное меню**", reply_markup=main_keyboard(), parse_mode="Markdown")

@user_router.message(F.text == "🔙 Назад")
async def back_to_profile(message: types.Message, state: FSMContext):
    await state.clear()
    await profile(message)

# ========== ВЫВЕСТИ ==========
@user_router.message(F.text == "💰 Вывести")
async def withdraw_start(message: types.Message, state: FSMContext):
    if is_banned(message.from_user.id):
        return
    user = get_user(message.from_user.id)
    if user["balance"] < 50:
        await message.answer("❌ Минимальная сумма вывода — **50 USDT**", parse_mode="Markdown")
        return
    
    await message.answer(
        "💸 **Введите сумму вывода (от 50 USDT):**",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(WithdrawState.amount)

@user_router.message(WithdrawState.amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await profile(message)
        return
    
    try:
        amount = float(message.text)
        if amount < 50:
            await message.answer("❌ Сумма должна быть **не менее 50 USDT**\nВведите другую сумму:", parse_mode="Markdown")
            return
        
        user = get_user(message.from_user.id)
        if amount > user["balance"]:
            await message.answer(f"❌ У вас {user['balance']} USDT\nВведите сумму не больше баланса:", parse_mode="Markdown")
            return
        
        await state.update_data(amount=amount)
        await message.answer(
            "💳 **Выберите способ вывода:**\n\n"
            "1️⃣ Карта\n"
            "2️⃣ Crypto Bot",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="💳 Карта")],
                    [types.KeyboardButton(text="🤖 Crypto Bot")],
                    [types.KeyboardButton(text="🔙 Назад")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(WithdrawState.method)
    except:
        await message.answer("❌ Введите число")

@user_router.message(WithdrawState.method)
async def withdraw_method(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await profile(message)
        return
    
    if message.text == "💳 Карта":
        await state.update_data(method="card")
        await message.answer(
            "💳 **Выберите тип перевода:**\n\n"
            "1️⃣ СБП (по номеру телефона)\n"
            "2️⃣ По номеру карты",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="📱 СБП")],
                    [types.KeyboardButton(text="💳 Номер карты")],
                    [types.KeyboardButton(text="🔙 Назад")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(WithdrawState.card_type)
    
    elif message.text == "🤖 Crypto Bot":
        await state.update_data(method="crypto")
        await message.answer(
            "🤖 **Отправьте ссылку на счёт из @CryptoBot**\n\n"
            "1. Перейдите в @CryptoBot\n"
            "2. Создайте счёт на оплату\n"
            "3. Пришлите ссылку сюда:",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.crypto_link)

@user_router.message(WithdrawState.card_type)
async def withdraw_card_type(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await profile(message)
        return
    
    if message.text == "📱 СБП":
        await state.update_data(card_type="sbp")
        await message.answer(
            "📱 **Введите номер телефона (привязанный к банку):**",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.phone)
    
    elif message.text == "💳 Номер карты":
        await state.update_data(card_type="card_number")
        await message.answer(
            "💳 **Введите номер карты (16 цифр):**",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.phone)

@user_router.message(WithdrawState.phone)
async def withdraw_phone(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await profile(message)
        return
    
    data = await state.get_data()
    if data.get("card_type") == "sbp":
        await state.update_data(phone=message.text)
        await message.answer(
            "🏦 **Введите название вашего банка:**",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.bank)
    else:
        await state.update_data(card_number=message.text)
        await message.answer(
            "👤 **Введите имя получателя (как на карте):**",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.name)

@user_router.message(WithdrawState.bank)
async def withdraw_bank(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await profile(message)
        return
    
    await state.update_data(bank=message.text)
    await message.answer(
        "👤 **Введите имя получателя:**",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(WithdrawState.name)

@user_router.message(WithdrawState.name)
async def withdraw_name(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await profile(message)
        return
    
    await state.update_data(name=message.text)
    await finish_withdraw(message, state)

@user_router.message(WithdrawState.crypto_link)
async def withdraw_crypto_link(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await profile(message)
        return
    
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
        f"📝 Реквизиты: {details}",
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

# ========== СПИСОК ЗАЯВОК ==========
@user_router.message(F.text == "📋 Список заявок")
async def list_user_withdraws(message: types.Message):
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
    
    if len(withdraws) > 10:
        text += f"\n📊 *Показаны последние 10 из {len(withdraws)}*"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

# ========== ОСТАВИТЬ ОТЗЫВ ==========
@user_router.message(F.text == "📝 Оставить отзыв")
async def review_start(message: types.Message, state: FSMContext):
    if is_banned(message.from_user.id):
        return
    await message.answer(
        "⭐ **Оцените наш сервис от 1 до 5:**",
        parse_mode="Markdown",
        reply_markup=rating_keyboard()
    )
    await state.set_state(ReviewState.rating)

@user_router.message(ReviewState.rating)
async def review_rating(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await go_main_menu(message, state)
        return
    
    rating_map = {
        "⭐ 1": 1, "⭐⭐ 2": 2, "⭐⭐⭐ 3": 3,
        "⭐⭐⭐⭐ 4": 4, "⭐⭐⭐⭐⭐ 5": 5
    }
    
    if message.text not in rating_map:
        await message.answer("❌ Пожалуйста, выберите оценку из кнопок")
        return
    
    rating = rating_map[message.text]
    await state.update_data(rating=rating)
    await message.answer(
        "💬 **Напишите ваш комментарий (или нажмите «Пропустить»):**",
        parse_mode="Markdown",
        reply_markup=review_skip_keyboard()
    )
    await state.set_state(ReviewState.comment)

@user_router.message(ReviewState.comment)
async def review_comment(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await review_start(message, state)
        return
    
    data = await state.get_data()
    rating = data["rating"]
    comment = None if message.text == "⏩ Пропустить" else message.text
    
    review = {
        "id": int(datetime.now().timestamp()),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now().isoformat()
    }
    add_review(review)
    
    # Отправка в канал
    stars = "⭐" * rating
    channel_text = (
        f"⭐ **Новый отзыв!**\n\n"
        f"👤 От: @{message.from_user.username}\n"
        f"⭐ Оценка: {rating}/5 {stars}\n"
        f"💬 Комментарий: {comment or 'Без комментария'}\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    try:
        await message.bot.send_message(REVIEWS_CHANNEL, channel_text, parse_mode="Markdown")
    except:
        pass
    
    # Уведомление админам
    await notify_admins(
        message.bot,
        f"⭐ **Новый отзыв!**\n\n"
        f"👤 От: @{message.from_user.username}\n"
        f"⭐ Оценка: {rating}/5\n"
        f"💬 Комментарий: {comment or 'Нет'}"
    )
    
    await state.clear()
    await message.answer(
        "✅ **Спасибо за ваш отзыв!**\n"
        "Мы ценим ваше мнение.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

# ========== ПОДДЕРЖКА ==========
@user_router.message(F.text == "🆘 Поддержка")
async def support(message: types.Message):
    if is_banned(message.from_user.id):
        return
    await message.answer(
        "📞 **Связь с администратором**\n\n"
        "Напишите ваш вопрос, и мы ответим вам в ближайшее время.",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )

@user_router.message(F.text)
async def support_message(message: types.Message):
    if is_banned(message.from_user.id):
        return
    if message.text in ["👤 Профиль", "📝 Оставить отзыв", "🆘 Поддержка", "ℹ️ ИНФО", "🔙 Назад", "🔙 Главное меню", "🏠 Главное меню", "💰 Вывести", "📋 Список заявок", "❌ Отмена", "⭐ 1", "⭐⭐ 2", "⭐⭐⭐ 3", "⭐⭐⭐⭐ 4", "⭐⭐⭐⭐⭐ 5", "⏩ Пропустить"]:
        return
    if message.from_user.id in ADMIN_IDS:
        return
    
    await notify_admins(
        message.bot,
        f"🆘 **Вопрос от пользователя!**\n\n"
        f"👤 От: @{message.from_user.username}\n"
        f"📝 Сообщение: {message.text}"
    )
    await message.answer(
        "✅ **Сообщение отправлено!**\n"
        "Администратор ответит вам в ближайшее время.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

# ========== ИНФО ==========
@user_router.message(F.text == "ℹ️ ИНФО")
async def info(message: types.Message):
    text = (
        "ℹ️ **ИНФОРМАЦИЯ**\n\n"
        "🕒 **График работы:**\n"
        "ПН-ПТ с 11:00 до 19:30\n\n"
        "💸 **Вывод средств:**\n"
        "Производится с 11:00 до 19:30\n\n"
        "💰 **Минимальная сумма вывода:** 50 USDT\n\n"
        "📞 **По всем вопросам:** /admin"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard())
