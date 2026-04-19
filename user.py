import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    register_user, load_banned, get_user_by_id, update_user_by_id,
    load_withdraws, save_withdraws, load_reviews, save_reviews,
    get_rating_list
)
from keyboards import (
    main_keyboard, profile_keyboard, back_keyboard, cancel_keyboard,
    rating_keyboard, skip_keyboard, anonymous_keyboard,
    withdraw_method_keyboard, pagination_keyboard
)
from utils import notify_admins
from config import ADMIN_IDS, REVIEWS_CHANNEL

user_router = Router()

class WithdrawStates(StatesGroup):
    waiting_amount = State()
    waiting_details = State()

class ReviewStates(StatesGroup):
    waiting_comment = State()

async def check_banned(user_id):
    return user_id in load_banned()

@user_router.message(Command("start"))
async def start(message: types.Message):
    await register_user(message.from_user)
    if await check_banned(message.from_user.id):
        await message.answer("❌ Вы забанены.")
        return
    
    await message.answer(
        "**🔥 Добро пожаловать!**\n\n"
        "👤 **ПРОФИЛЬ** - баланс и выводы\n"
        "📜 **ИСТОРИЯ ВЫВОДОВ** - все ваши выводы\n"
        "⭐ **ОСТАВИТЬ ОТЗЫВ** - оцените наш сервис\n"
        "💰 **ВЫВОД СРЕДСТВ** - вывести деньги\n"
        "ℹ️ **ИНФО** - информация о работе\n"
        "🆘 **ПОДДЕРЖКА** - связаться с админом",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@user_router.message(lambda msg: msg.text == "🏠 Главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 **Главное меню**", reply_markup=main_keyboard(), parse_mode="Markdown")

@user_router.message(lambda msg: msg.text == "🔙 Назад")
async def back_button(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 **Назад**", reply_markup=main_keyboard(), parse_mode="Markdown")

@user_router.message(lambda msg: msg.text == "❌ Отмена")
async def cancel_button(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ **Действие отменено**", reply_markup=main_keyboard(), parse_mode="Markdown")

# ========== ПРОФИЛЬ ==========
@user_router.message(lambda msg: msg.text == "👤 ПРОФИЛЬ")
async def profile(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    
    user = get_user_by_id(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка, попробуйте /start")
        return
    
    rating_list = get_rating_list()
    rating_place = 0
    for i, u in enumerate(rating_list, 1):
        if u["id"] == message.from_user.id:
            rating_place = i
            break
    
    avg_score = 0
    if user.get("rating_count", 0) > 0:
        avg_score = user.get("rating_score", 0) / user.get("rating_count", 0)
    
    stars = "⭐" * round(avg_score) if avg_score > 0 else "нет"
    
    text = (
        f"**👤 ВАШ ПРОФИЛЬ**\n\n"
        f"💰 **Баланс:** {user['balance']} USDT\n"
        f"📤 **Выведено всего:** {user['total_withdrawn']} USDT\n\n"
        f"🏆 **Рейтинг:** {rating_place if rating_place > 0 else '0'}\n"
        f"⭐ **Средняя оценка:** {avg_score:.1f}/5 {stars}\n"
        f"📊 **Отзывов оставлено:** {user.get('rating_count', 0)}\n\n"
        f"🆔 **ID:** {user['id']}\n"
        f"👤 **Username:** @{user['username'] or 'нет'}"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

# ========== ИСТОРИЯ ВЫВОДОВ ==========
@user_router.message(lambda msg: msg.text == "📜 ИСТОРИЯ ВЫВОДОВ")
async def withdraw_history(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    
    withdraws = load_withdraws()
    user_withdraws = [w for w in withdraws if w["user_id"] == message.from_user.id]
    user_withdraws.reverse()
    
    if not user_withdraws:
        await message.answer("📜 **У вас пока нет заявок на вывод.**", reply_markup=profile_keyboard(), parse_mode="Markdown")
        return
    
    await show_withdraw_page(message, user_withdraws, 1)

async def show_withdraw_page(message: types.Message, withdraws, page: int):
    items_per_page = 5
    total_pages = (len(withdraws) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    current = withdraws[start:end]
    
    status_emoji = {
        "pending": "⏳ В ожидании",
        "approved": "✅ Одобрено",
        "rejected": "❌ Отклонено"
    }
    
    text = f"📜 **ИСТОРИЯ ВЫВОДОВ (стр. {page}/{total_pages})**\n\n"
    for w in current:
        date = w.get("created_at", "")[:10]
        text += f"• **{w['amount']} USDT** | {date} | {status_emoji.get(w['status'], '⏳ В ожидании')}\n"
    
    kb = pagination_keyboard(page, total_pages, "withdraw")
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

# ========== ВЫВОД СРЕДСТВ ==========
@user_router.message(lambda msg: msg.text == "💰 ВЫВОД СРЕДСТВ")
async def withdraw_start(message: types.Message, state: FSMContext):
    if await check_banned(message.from_user.id):
        return
    
    user = get_user_by_id(message.from_user.id)
    if user['balance'] <= 0:
        await message.answer("❌ **У вас недостаточно средств для вывода.**", reply_markup=profile_keyboard(), parse_mode="Markdown")
        return
    
    await message.answer(
        f"💰 **Ваш баланс: {user['balance']} USDT**\n\n"
        f"💵 **Введите сумму для вывода (мин. 10 USDT):**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(WithdrawStates.waiting_amount)

@user_router.message(WithdrawStates.waiting_amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ **Вывод отменен**", reply_markup=main_keyboard(), parse_mode="Markdown")
        return
    
    try:
        amount = float(message.text)
        user = get_user_by_id(message.from_user.id)
        
        if amount < 10:
            await message.answer("❌ **Минимальная сумма вывода — 10 USDT**\nВведите другую сумму:", parse_mode="Markdown")
            return
        if amount > user['balance']:
            await message.answer(f"❌ **У вас {user['balance']} USDT**\nВведите сумму не больше баланса:", parse_mode="Markdown")
            return
        
        await state.update_data(amount=amount)
        await message.answer(
            "💳 **Выберите способ получения:**",
            reply_markup=withdraw_method_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(WithdrawStates.waiting_details)
    except:
        await message.answer("❌ **Введите число (цифрами)**", parse_mode="Markdown")

@user_router.callback_query(lambda c: c.data.startswith("withdraw_"))
async def withdraw_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    await state.update_data(method=method)
    
    if method == "card":
        await callback.message.edit_text("💳 **Введите номер банковской карты для перевода:**", parse_mode="Markdown")
        await state.set_state(WithdrawStates.waiting_details)
    elif method == "crypto":
        await callback.message.edit_text(
            "₿ **КРИПТОКОШЕЛЁК (USDT)**\n\n"
            "1️⃣ Перейдите в @CryptoBot\n"
            "2️⃣ Создайте счёт на оплату в USDT\n"
            "3️⃣ **Пришлите ссылку на оплату сюда:**",
            parse_mode="Markdown"
        )
        await state.set_state(WithdrawStates.waiting_details)
    elif method == "contact":
        await callback.message.edit_text("📞 **Заявка на связь с администратором отправлена!**", parse_mode="Markdown")
        await notify_admins(callback.bot, f"📞 **Пользователь @{callback.from_user.username} хочет связаться по вопросу вывода**")
        await state.clear()
        await callback.bot.send_message(callback.from_user.id, "✅ **Администратор свяжется с вами в ближайшее время.**", reply_markup=main_keyboard(), parse_mode="Markdown")
    
    await callback.answer()

@user_router.message(WithdrawStates.waiting_details)
async def withdraw_details(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ **Вывод отменен**", reply_markup=main_keyboard(), parse_mode="Markdown")
        return
    
    data = await state.get_data()
    amount = data.get("amount")
    method = data.get("method")
    details = message.text
    
    method_name = "Банковская карта" if method == "card" else "Криптокошелёк (USDT)"
    
    withdraw = {
        "id": int(datetime.now().timestamp()),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "amount": amount,
        "method": method_name,
        "details": details,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    withdraws = load_withdraws()
    withdraws.append(withdraw)
    save_withdraws(withdraws)
    
    await notify_admins(
        message.bot,
        f"💰 **НОВАЯ ЗАЯВКА НА ВЫВОД!**\n\n"
        f"👤 **От:** @{message.from_user.username or 'нет'} (ID: {message.from_user.id})\n"
        f"💵 **Сумма:** {amount} USDT\n"
        f"💳 **Способ:** {method_name}\n"
        f"📝 **Реквизиты:** {details}",
        reply_markup=withdraw_action_keyboard(withdraw["id"])
    )
    
    await state.clear()
    await message.answer(
        f"✅ **Заявка на вывод {amount} USDT отправлена!**\n\n"
        f"⏳ **Администратор рассмотрит её в ближайшее время.**",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

def withdraw_action_keyboard(wid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_withdraw_{wid}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_withdraw_{wid}")]
    ])

# ========== ОСТАВИТЬ ОТЗЫВ ==========
@user_router.message(lambda msg: msg.text == "⭐ ОСТАВИТЬ ОТЗЫВ")
async def leave_review(message: types.Message, state: FSMContext):
    if await check_banned(message.from_user.id):
        return
    
    await message.answer(
        "⭐ **На сколько вы оцениваете наш сервис?**",
        parse_mode="Markdown",
        reply_markup=rating_keyboard()
    )

@user_router.callback_query(lambda c: c.data.startswith("rating_"))
async def get_rating(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    
    if rating <= 3:
        await callback.message.edit_text(
            "⚠️ **Пожалуйста, напишите, что вам не понравилось?**\n\n"
            "Или нажмите «Пропустить»:",
            parse_mode="Markdown",
            reply_markup=skip_keyboard()
        )
    else:
        await callback.message.edit_text(
            "😊 **Хотите добавить что-то?**\n\n"
            "Напишите, и мы обязательно будем рады вашему мнению!\n"
            "Или нажмите «Пропустить»:",
            parse_mode="Markdown",
            reply_markup=skip_keyboard()
        )
    await state.set_state(ReviewStates.waiting_comment)
    await callback.answer()

@user_router.callback_query(lambda c: c.data == "review_skip")
async def review_skip(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await callback.message.edit_text("📢 **Выберите, как отправить отзыв:**", reply_markup=anonymous_keyboard(), parse_mode="Markdown")
    await callback.answer()

@user_router.callback_query(lambda c: c.data == "review_write")
async def review_write(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ **Напишите ваш комментарий:**", reply_markup=cancel_keyboard(), parse_mode="Markdown")
    await state.set_state(ReviewStates.waiting_comment)
    await callback.answer()

@user_router.message(ReviewStates.waiting_comment)
async def review_comment(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ **Отзыв отменен**", reply_markup=main_keyboard(), parse_mode="Markdown")
        return
    
    await state.update_data(comment=message.text)
    await message.answer("📢 **Выберите, как отправить отзыв:**", reply_markup=anonymous_keyboard(), parse_mode="Markdown")

@user_router.callback_query(lambda c: c.data.startswith("review_"))
async def review_send(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "review_cancel":
        await state.clear()
        await callback.message.edit_text("❌ **Отзыв отменен**", reply_markup=main_keyboard())
        await callback.answer()
        return
    
    data = await state.get_data()
    rating = data.get("rating")
    comment = data.get("comment")
    is_anonymous = callback.data == "review_anonymous"
    
    review = {
        "id": int(datetime.now().timestamp()),
        "user_id": callback.from_user.id if not is_anonymous else None,
        "username": callback.from_user.username if not is_anonymous else None,
        "rating": rating,
        "comment": comment,
        "is_anonymous": is_anonymous,
        "created_at": datetime.now().isoformat()
    }
    reviews = load_reviews()
    reviews.append(review)
    save_reviews(reviews)
    
    user = get_user_by_id(callback.from_user.id)
    new_count = user.get("rating_count", 0) + 1
    new_score = user.get("rating_score", 0) + rating
    update_user_by_id(callback.from_user.id, {"rating_count": new_count, "rating_score": new_score})
    
    stars = "⭐" * rating
    channel_text = (
        f"⭐ **НОВЫЙ ОТЗЫВ!**\n\n"
        f"👤 **{'Аноним' if is_anonymous else f'@{callback.from_user.username}'}**\n"
        f"⭐ **Оценка:** {rating}/5 {stars}\n"
    )
    if comment:
        channel_text += f"💬 **Комментарий:** {comment}\n"
    channel_text += f"\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    try:
        await callback.bot.send_message(REVIEWS_CHANNEL, channel_text, parse_mode="Markdown")
    except:
        pass
    
    admin_text = (
        f"⭐ **НОВЫЙ ОТЗЫВ!**\n\n"
        f"👤 **{'Аноним' if is_anonymous else f'@{callback.from_user.username} (ID: {callback.from_user.id})'}**\n"
        f"⭐ **Оценка:** {rating}/5\n"
    )
    if comment:
        admin_text += f"💬 **Комментарий:** {comment}\n"
    await notify_admins(callback.bot, admin_text)
    
    await state.clear()
    await callback.message.edit_text("✅ **Спасибо за ваш отзыв!**", reply_markup=main_keyboard(), parse_mode="Markdown")
    await callback.answer()

# ========== ИНФО ==========
@user_router.message(lambda msg: msg.text == "ℹ️ ИНФО")
async def info(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    
    text = (
        "ℹ️ **ИНФОРМАЦИЯ О РАБОТЕ**\n\n"
        "🕒 **График работы:**\n"
        "ПН-ПТ с 11:00 до 19:30\n"
        "(Суббота иногда)\n\n"
        "💸 **Вывод средств:**\n"
        "Производится с 11:00 до 19:30\n\n"
        "❌ **Отклонение заявки:**\n"
        "Если ваша заявка отклонена — обратитесь к администратору\n\n"
        "⭐ **Наши отзывы:**\n"
        "https://t.me/otzyvOPK\n\n"
        "📢 **Подробная информация:**\n"
        "О прайсах и всём остальном можно узнать в нашем канале:\n"
        "👉 https://t.me/+ZAJelSN78aliNzIx\n\n"
        "📞 **По всем вопросам:** /admin"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard())

# ========== ПОДДЕРЖКА ==========
@user_router.message(lambda msg: msg.text == "🆘 ПОДДЕРЖКА")
async def support(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    
    await message.answer(
        "📞 **СВЯЗЬ С АДМИНИСТРАТОРОМ**\n\n"
        "Напишите ваш вопрос, и мы ответим вам в ближайшее время.\n\n"
        "✅ **Администратор свяжется с вами анонимно через бота.**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )

@user_router.message(lambda msg: msg.text not in ["🏠 Главное меню", "🔙 Назад", "❌ Отмена"] and msg.text not in ["👤 ПРОФИЛЬ", "📜 ИСТОРИЯ ВЫВОДОВ", "⭐ ОСТАВИТЬ ОТЗЫВ", "💰 ВЫВОД СРЕДСТВ", "ℹ️ ИНФО", "🆘 ПОДДЕРЖКА"])
async def support_message(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    
    await notify_admins(
        message.bot,
        f"🆘 **ОБРАЩЕНИЕ В ПОДДЕРЖКУ!**\n\n"
        f"👤 **От:** @{message.from_user.username or 'нет'} (ID: {message.from_user.id})\n"
        f"📝 **Сообщение:** {message.text}"
    )
    await message.answer("✅ **Сообщение отправлено! Администратор ответит вам в ближайшее время.**", reply_markup=main_keyboard(), parse_mode="Markdown")

# Пагинация
@user_router.callback_query(lambda c: c.data.startswith("withdraw_page_"))
async def withdraw_page_callback(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    withdraws = load_withdraws()
    user_withdraws = [w for w in withdraws if w["user_id"] == callback.from_user.id]
    user_withdraws.reverse()
    await show_withdraw_page(callback.message, user_withdraws, page)
    await callback.answer()

@user_router.callback_query(lambda c: c.data == "to_main_menu")
async def to_main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 **Главное меню**", reply_markup=main_keyboard(), parse_mode="Markdown")
    await callback.answer()
