from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import register_user, get_user_by_id, is_banned, get_rating_list, load_withdraws
from keyboards import main_keyboard, profile_keyboard, pagination_keyboard
from utils import notify_admins

user_router = Router()

class WithdrawState(StatesGroup):
    amount = State()
    details = State()

@user_router.message(Command("start"))
async def start_cmd(message: types.Message):
    register_user(message.from_user)
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы забанены")
        return
    await message.answer(
        "🔥 **Добро пожаловать!**\n\n"
        "👤 Профиль - баланс и выводы\n"
        "📜 История выводов - все операции\n"
        "⭐ Оставить отзыв - оцените нас\n"
        "💰 Вывод средств - вывести деньги\n"
        "ℹ️ Инфо - информация\n"
        "🆘 Поддержка - связаться с админом",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@user_router.message(F.text == "🔙 Назад")
async def back_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 Назад", reply_markup=main_keyboard())

@user_router.message(F.text == "❌ Отмена")
async def cancel_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=main_keyboard())

@user_router.message(F.text == "👤 Профиль")
async def profile_cmd(message: types.Message):
    if is_banned(message.from_user.id):
        return
    user = get_user_by_id(message.from_user.id)
    rating_list = get_rating_list()
    place = 0
    for i, u in enumerate(rating_list, 1):
        if u["id"] == message.from_user.id:
            place = i
            break
    avg = 0
    if user.get("rating_count", 0) > 0:
        avg = user["rating_score"] / user["rating_count"]
    stars = "⭐" * round(avg) if avg > 0 else ""
    text = (
        f"👤 **Профиль**\n\n"
        f"💰 Баланс: {user['balance']} USDT\n"
        f"📤 Выведено: {user['total_withdrawn']} USDT\n"
        f"🏆 Рейтинг: {place}\n"
        f"⭐ Оценка: {avg:.1f}/5 {stars}\n"
        f"📊 Отзывов: {user.get('rating_count', 0)}\n"
        f"🆔 ID: {user['id']}\n"
        f"👤 @{user['username'] or 'нет'}"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

@user_router.message(F.text == "📜 История выводов")
async def history_cmd(message: types.Message):
    if is_banned(message.from_user.id):
        return
    withdraws = load_withdraws()
    my = [w for w in withdraws if w["user_id"] == message.from_user.id]
    my.reverse()
    if not my:
        await message.answer("📜 История пуста", reply_markup=profile_keyboard())
        return
    await show_history(message, my, 1)

async def show_history(message, data, page):
    per_page = 5
    total = (len(data) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    current = data[start:end]
    status_map = {"pending": "⏳ Ожидание", "approved": "✅ Одобрено", "rejected": "❌ Отклонено"}
    text = f"📜 **История (стр. {page}/{total})**\n\n"
    for w in current:
        text += f"• {w['amount']} USDT - {w['created_at'][:10]} - {status_map.get(w['status'], '⏳ Ожидание')}\n"
    await message.answer(text, parse_mode="Markdown", reply_markup=pagination_keyboard(page, total, "history"))

@user_router.message(F.text == "ℹ️ Инфо")
async def info_cmd(message: types.Message):
    text = (
        "ℹ️ **Информация**\n\n"
        "🕒 Работа: ПН-ПТ 11:00-19:30\n"
        "💸 Выводы: с 11:00 до 19:30\n"
        "⭐ Отзывы: https://t.me/otzyvOPK\n"
        "📢 Канал: https://t.me/+ZAJelSN78aliNzIx"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard())

@user_router.message(F.text == "🆘 Поддержка")
async def support_cmd(message: types.Message):
    await message.answer("📞 Напишите ваш вопрос. Администратор ответит.", reply_markup=cancel_keyboard())

@user_router.message(F.text)
async def support_msg_cmd(message: types.Message):
    if is_banned(message.from_user.id):
        return
    if message.text in ["👤 Профиль", "📜 История выводов", "⭐ Оставить отзыв", "💰 Вывод средств", "ℹ️ Инфо", "🆘 Поддержка", "🔙 Назад", "❌ Отмена"]:
        return
    await notify_admins(message.bot, f"🆘 Вопрос от @{message.from_user.username}\n\n{message.text}")
    await message.answer("✅ Отправлено!", reply_markup=main_keyboard())

@user_router.callback_query(lambda c: c.data.startswith("history_"))
async def history_page_callback(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[1])
    withdraws = load_withdraws()
    my = [w for w in withdraws if w["user_id"] == callback.from_user.id]
    my.reverse()
    await show_history(callback.message, my, page)
    await callback.answer()

@user_router.callback_query(lambda c: c.data == "to_main")
async def to_main_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 Главное меню", reply_markup=main_keyboard())
    await callback.answer()
