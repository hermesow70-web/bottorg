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
    main_keyboard, profile_keyboard, back_keyboard, withdraw_amount_keyboard,
    withdraw_method_keyboard, withdraw_card_type_keyboard,
    rating_keyboard, review_skip_keyboard, support_keyboard
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

async def notify_admins(bot, text, reply_markup=None):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown", reply_markup=reply_markup)
        except:
            pass

@user_router.message(Command("start"))
async def start(message: types.Message):
    register_user(message.from_user.id, message.from_user.username)
    if is_banned(message.from_user.id):
        await message.answer("❌ ВЫ ЗАБАНЕНЫ")
        return
    await message.answer(
        "🔥 **ДОБРО ПОЖАЛОВАТЬ!**\n\n"
        "ВЫБЕРИТЕ ДЕЙСТВИЕ:",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@user_router.message(F.text == "👤 ПРОФИЛЬ")
async def profile(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("❌ ВЫ ЗАБАНЕНЫ")
        return
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ ОШИБКА, ПОПРОБУЙТЕ /start")
        return
    
    active_count = get_active_requests_count(message.from_user.id)
    
    text = (
        f"👤 **ВАШ ПРОФИЛЬ**\n\n"
        f"💰 **БАЛАНС:** {user['balance']} USDT\n"
        f"📋 **АКТИВНЫХ ЗАЯВОК:** {active_count}\n"
        f"📤 **ВЫВЕДЕНО ВСЕГО:** {user['total_withdrawn']} USDT"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

@user_router.message(F.text == "◀️ НАЗАД")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("◀️ ГЛАВНОЕ МЕНЮ", reply_markup=main_keyboard())

@user_router.message(F.text == "💰 ВЫВЕСТИ")
async def withdraw_start(message: types.Message, state: FSMContext):
    if is_banned(message.from_user.id):
        return
    user = get_user(message.from_user.id)
    if user["balance"] < 50:
        await message.answer("❌ МИНИМАЛЬНАЯ СУММА ВЫВОДА — **50 USDT**", parse_mode="Markdown")
        return
    
    await message.answer(
        "💸 **ВВЕДИТЕ СУММУ ВЫВОДА (ОТ 50 USDT):**",
        parse_mode="Markdown",
        reply_markup=withdraw_amount_keyboard()
    )
    await state.set_state(WithdrawState.amount)

@user_router.message(WithdrawState.amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await profile(message)
        return
    
    try:
        amount = float(message.text)
        if amount < 50:
            await message.answer("❌ СУММА ДОЛЖНА БЫТЬ **НЕ МЕНЕЕ 50 USDT**\nВВЕДИТЕ ДРУГУЮ СУММУ:", parse_mode="Markdown")
            return
        
        user = get_user(message.from_user.id)
        if amount > user["balance"]:
            await message.answer(f"❌ У ВАС {user['balance']} USDT\nВВЕДИТЕ СУММУ НЕ БОЛЬШЕ БАЛАНСА:", parse_mode="Markdown")
            return
        
        await state.update_data(amount=amount)
        await message.answer(
            "💳 **ВЫБЕРИТЕ СПОСОБ ВЫВОДА:**",
            parse_mode="Markdown",
            reply_markup=withdraw_method_keyboard()
        )
        await state.set_state(WithdrawState.method)
    except:
        await message.answer("❌ ВВЕДИТЕ ЧИСЛО")

@user_router.message(WithdrawState.method)
async def withdraw_method(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await profile(message)
        return
    
    if message.text == "💳 КАРТА":
        await state.update_data(method="card")
        await message.answer(
            "💳 **ВЫБЕРИТЕ ТИП ПЕРЕВОДА:**",
            parse_mode="Markdown",
            reply_markup=withdraw_card_type_keyboard()
        )
        await state.set_state(WithdrawState.card_type)
    
    elif message.text == "🤖 CRYPTO BOT":
        await state.update_data(method="crypto")
        await message.answer(
            "🤖 **ОТПРАВЬТЕ ССЫЛКУ НА СЧЁТ ИЗ @CryptoBot**\n\n"
            "1. ПЕРЕЙДИТЕ В @CryptoBot\n"
            "2. СОЗДАЙТЕ СЧЁТ НА ОПЛАТУ\n"
            "3. ПРИШЛИТЕ ССЫЛКУ СЮДА:",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.crypto_link)

@user_router.message(WithdrawState.card_type)
async def withdraw_card_type(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await profile(message)
        return
    
    if message.text == "📱 СБП":
        await state.update_data(card_type="sbp")
        await message.answer(
            "📱 **ВВЕДИТЕ НОМЕР ТЕЛЕФОНА (ПРИВЯЗАННЫЙ К БАНКУ):**",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.phone)
    
    elif message.text == "💳 НОМЕР КАРТЫ":
        await state.update_data(card_type="card_number")
        await message.answer(
            "💳 **ВВЕДИТЕ НОМЕР КАРТЫ (16 ЦИФР):**",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.phone)

@user_router.message(WithdrawState.phone)
async def withdraw_phone(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await profile(message)
        return
    
    data = await state.get_data()
    if data.get("card_type") == "sbp":
        await state.update_data(phone=message.text)
        await message.answer(
            "🏦 **ВВЕДИТЕ НАЗВАНИЕ ВАШЕГО БАНКА:**",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.bank)
    else:
        await state.update_data(card_number=message.text)
        await message.answer(
            "👤 **ВВЕДИТЕ ИМЯ ПОЛУЧАТЕЛЯ (КАК НА КАРТЕ):**",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(WithdrawState.name)

@user_router.message(WithdrawState.bank)
async def withdraw_bank(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await profile(message)
        return
    
    await state.update_data(bank=message.text)
    await message.answer(
        "👤 **ВВЕДИТЕ ИМЯ ПОЛУЧАТЕЛЯ:**",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(WithdrawState.name)

@user_router.message(WithdrawState.name)
async def withdraw_name(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await profile(message)
        return
    
    await state.update_data(name=message.text)
    await finish_withdraw(message, state)

@user_router.message(WithdrawState.crypto_link)
async def withdraw_crypto_link(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
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
            details = f"СБП\nТЕЛЕФОН: {data['phone']}\nБАНК: {data['bank']}\nИМЯ: {data['name']}"
        else:
            details = f"НОМЕР КАРТЫ: {data['card_number']}\nИМЯ: {data['name']}"
    else:
        details = f"CRYPTO BOT ССЫЛКА: {data['crypto_link']}"
    
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
    
    from keyboards import withdraw_action_keyboard
    await notify_admins(
        message.bot,
        f"💰 **НОВАЯ ЗАЯВКА НА ВЫВОД!**\n\n"
        f"👤 ОТ: @{message.from_user.username}\n"
        f"💵 СУММА: {amount} USDT\n"
        f"💳 СПОСОБ: {method}\n"
        f"📝 РЕКВИЗИТЫ:\n{details}",
        withdraw_action_keyboard(withdraw["id"])
    )
    
    await message.answer(
        f"✅ **ЗАЯВКА НА ВЫВОД {amount} USDT ОТПРАВЛЕНА!**\n\n"
        f"⏳ СТАТУС: **В ОЖИДАНИИ**\n"
        f"АДМИНИСТРАТОР РАССМОТРИТ ЕЁ В БЛИЖАЙШЕЕ ВРЕМЯ.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    
    await state.clear()

@user_router.message(F.text == "📋 МОИ ЗАЯВКИ")
async def list_user_withdraws(message: types.Message):
    if is_banned(message.from_user.id):
        return
    withdraws = get_user_withdraws(message.from_user.id)
    if not withdraws:
        await message.answer("📭 **У ВАС НЕТ ЗАЯВОК НА ВЫВОД**", parse_mode="Markdown", reply_markup=profile_keyboard())
        return
    
    withdraws.reverse()
    text = "📋 **ВАШИ ЗАЯВКИ НА ВЫВОД:**\n\n"
    status_map = {"pending": "⏳ В ОЖИДАНИИ", "approved": "✅ ОДОБРЕНО", "rejected": "❌ ОТКЛОНЕНО"}
    
    for w in withdraws[:10]:
        text += f"• {w['amount']} USDT - {status_map.get(w['status'], '⏳ В ОЖИДАНИИ')} - {w['created_at'][:10]}\n"
    
    if len(withdraws) > 10:
        text += f"\n📊 *ПОКАЗАНЫ ПОСЛЕДНИЕ 10 ИЗ {len(withdraws)}*"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

@user_router.message(F.text == "📝 ОТЗЫВ")
async def review_start(message: types.Message, state: FSMContext):
    if is_banned(message.from_user.id):
        return
    await message.answer(
        "⭐ **ОЦЕНИТЕ НАШ СЕРВИС ОТ 1 ДО 5:**",
        parse_mode="Markdown",
        reply_markup=rating_keyboard()
    )
    await state.set_state(ReviewState.rating)

@user_router.message(ReviewState.rating)
async def review_rating(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await start(message)
        return
    
    rating_map = {
        "⭐ 1": 1, "⭐⭐ 2": 2, "⭐⭐⭐ 3": 3,
        "⭐⭐⭐⭐ 4": 4, "⭐⭐⭐⭐⭐ 5": 5
    }
    
    if message.text not in rating_map:
        await message.answer("❌ ПОЖАЛУЙСТА, ВЫБЕРИТЕ ОЦЕНКУ ИЗ КНОПОК")
        return
    
    rating = rating_map[message.text]
    await state.update_data(rating=rating)
    await message.answer(
        "💬 **НАПИШИТЕ ВАШ КОММЕНТАРИЙ (ИЛИ НАЖМИТЕ «ПРОПУСТИТЬ»):**",
        parse_mode="Markdown",
        reply_markup=review_skip_keyboard()
    )
    await state.set_state(ReviewState.comment)

@user_router.message(ReviewState.comment)
async def review_comment(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await review_start(message, state)
        return
    
    data = await state.get_data()
    rating = data["rating"]
    comment = None if message.text == "⏩ ПРОПУСТИТЬ" else message.text
    
    review = {
        "id": int(datetime.now().timestamp()),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now().isoformat()
    }
    add_review(review)
    
    stars = "⭐" * rating
    channel_text = (
        f"⭐ **НОВЫЙ ОТЗЫВ!**\n\n"
        f"👤 ОТ: @{message.from_user.username}\n"
        f"⭐ ОЦЕНКА: {rating}/5 {stars}\n"
        f"💬 КОММЕНТАРИЙ: {comment or 'БЕЗ КОММЕНТАРИЯ'}\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    try:
        await message.bot.send_message(REVIEWS_CHANNEL, channel_text, parse_mode="Markdown")
    except:
        pass
    
    await notify_admins(
        message.bot,
        f"⭐ **НОВЫЙ ОТЗЫВ!**\n\n"
        f"👤 ОТ: @{message.from_user.username}\n"
        f"⭐ ОЦЕНКА: {rating}/5\n"
        f"💬 КОММЕНТАРИЙ: {comment or 'НЕТ'}"
    )
    
    await state.clear()
    await message.answer(
        "✅ **СПАСИБО ЗА ВАШ ОТЗЫВ!**\n"
        "МЫ ЦЕНИМ ВАШЕ МНЕНИЕ.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@user_router.message(F.text == "🆘 ПОДДЕРЖКА")
async def support(message: types.Message):
    if is_banned(message.from_user.id):
        return
    await message.answer(
        "📞 **СВЯЗЬ С АДМИНИСТРАТОРОМ**\n\n"
        "НАПИШИТЕ ВАШ ВОПРОС, И МЫ ОТВЕТИМ ВАМ В БЛИЖАЙШЕЕ ВРЕМЯ.",
        parse_mode="Markdown",
        reply_markup=support_keyboard()
    )

@user_router.message(F.text == "ℹ️ ИНФО")
async def info(message: types.Message):
    text = (
        "ℹ️ **ИНФОРМАЦИЯ**\n\n"
        "🕒 **ГРАФИК РАБОТЫ:**\n"
        "ПН-ПТ С 11:00 ДО 19:30\n\n"
        "💸 **ВЫВОД СРЕДСТВ:**\n"
        "ПРОИЗВОДИТСЯ С 11:00 ДО 19:30\n\n"
        "💰 **МИНИМАЛЬНАЯ СУММА ВЫВОДА:** 50 USDT\n\n"
        "📞 **ПО ВСЕМ ВОПРОСАМ:** /admin"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard())

@user_router.message(F.text)
async def support_message(message: types.Message):
    if is_banned(message.from_user.id):
        return
    if message.from_user.id in ADMIN_IDS:
        return
    if message.text in ["👤 ПРОФИЛЬ", "📝 ОТЗЫВ", "🆘 ПОДДЕРЖКА", "ℹ️ ИНФО", "◀️ НАЗАД", "💰 ВЫВЕСТИ", "📋 МОИ ЗАЯВКИ", "⭐ 1", "⭐⭐ 2", "⭐⭐⭐ 3", "⭐⭐⭐⭐ 4", "⭐⭐⭐⭐⭐ 5", "⏩ ПРОПУСТИТЬ", "💳 КАРТА", "🤖 CRYPTO BOT", "📱 СБП", "💳 НОМЕР КАРТЫ"]:
        return
    
    await notify_admins(
        message.bot,
        f"🆘 **ВОПРОС ОТ ПОЛЬЗОВАТЕЛЯ!**\n\n"
        f"👤 ОТ: @{message.from_user.username}\n"
        f"📝 СООБЩЕНИЕ: {message.text}"
    )
    await message.answer(
        "✅ **СООБЩЕНИЕ ОТПРАВЛЕНО!**\n"
        "АДМИНИСТРАТОР ОТВЕТИТ ВАМ В БЛИЖАЙШЕЕ ВРЕМЯ.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
