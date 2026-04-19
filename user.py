from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import register_user, get_user_by_id, is_banned, get_rating_list, load_withdraws, load_reviews
from keyboards import main_keyboard, profile_keyboard, back_keyboard, cancel_keyboard, pagination_keyboard
from utils import notify_admins
from config import REVIEWS_CHANNEL

user_router = Router()

class WithdrawState(StatesGroup):
    amount = State()
    details = State()

class ReviewState(StatesGroup):
    rating = State()
    comment = State()

@user_router.message(Command("start"))
async def start(message: types.Message):
    register_user(message.from_user)
    if is_banned(message.from_user.id):
        await message.answer("❌ ВЫ ЗАБАНЕНЫ")
        return
    await message.answer(
        "🔥 **ДОБРО ПОЖАЛОВАТЬ!**\n\n"
        "👤 ПРОФИЛЬ - баланс и выводы\n"
        "📜 ИСТОРИЯ ВЫВОДОВ - все операции\n"
        "⭐ ОСТАВИТЬ ОТЗЫВ - оцените нас\n"
        "💰 ВЫВОД СРЕДСТВ - вывести деньги\n"
        "ℹ️ ИНФО - информация\n"
        "🆘 ПОДДЕРЖКА - связаться с админом",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@user_router.message(lambda msg: msg.text == "🔙 НАЗАД")
async def back_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 НАЗАД", reply_markup=main_keyboard())

@user_router.message(lambda msg: msg.text == "❌ ОТМЕНА")
async def cancel_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ ОТМЕНЕНО", reply_markup=main_keyboard())

# ========== ПРОФИЛЬ ==========
@user_router.message(lambda msg: msg.text == "👤 ПРОФИЛЬ")
async def profile(message: types.Message):
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
    text = f"👤 **ПРОФИЛЬ**\n\n💰 БАЛАНС: {user['balance']} USDT\n📤 ВЫВЕДЕНО: {user['total_withdrawn']} USDT\n🏆 РЕЙТИНГ: {place}\n⭐ ОЦЕНКА: {avg:.1f}/5 {stars}\n📊 ОТЗЫВОВ: {user.get('rating_count', 0)}\n🆔 ID: {user['id']}\n👤 @{user['username'] or 'нет'}"
    await message.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

# ========== ИСТОРИЯ ВЫВОДОВ ==========
@user_router.message(lambda msg: msg.text == "📜 ИСТОРИЯ ВЫВОДОВ")
async def history(message: types.Message):
    if is_banned(message.from_user.id):
        return
    withdraws = load_withdraws()
    my = [w for w in withdraws if w["user_id"] == message.from_user.id]
    my.reverse()
    if not my:
        await message.answer("📜 ИСТОРИЯ ПУСТА", reply_markup=profile_keyboard())
        return
    await show_history(message, my, 1)

async def show_history(message, data, page):
    per_page = 5
    total = (len(data) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    current = data[start:end]
    status_map = {"pending": "⏳ ОЖИДАНИЕ", "approved": "✅ ОДОБРЕНО", "rejected": "❌ ОТКЛОНЕНО"}
    text = f"📜 **ИСТОРИЯ (СТР. {page}/{total})**\n\n"
    for w in current:
        text += f"• {w['amount']} USDT - {w['created_at'][:10]} - {status_map.get(w['status'], '⏳ ОЖИДАНИЕ')}\n"
    await message.answer(text, parse_mode="Markdown", reply_markup=pagination_keyboard(page, total, "history"))

# ========== ИНФО ==========
@user_router.message(lambda msg: msg.text == "ℹ️ ИНФО")
async def info(message: types.Message):
    text = "ℹ️ **ИНФОРМАЦИЯ**\n\n🕒 РАБОТА: ПН-ПТ 11:00-19:30\n💸 ВЫВОДЫ: С 11:00 ДО 19:30\n⭐ ОТЗЫВЫ: https://t.me/otzyvOPK\n📢 КАНАЛ: https://t.me/+ZAJelSN78aliNzIx"
    await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard())

# ========== ПОДДЕРЖКА ==========
@user_router.message(lambda msg: msg.text == "🆘 ПОДДЕРЖКА")
async def support(message: types.Message):
    await message.answer("📞 НАПИШИТЕ ВАШ ВОПРОС. АДМИНИСТРАТОР ОТВЕТИТ.", reply_markup=cancel_keyboard())

@user_router.message(lambda msg: msg.text not in ["👤 ПРОФИЛЬ", "📜 ИСТОРИЯ ВЫВОДОВ", "⭐ ОСТАВИТЬ ОТЗЫВ", "💰 ВЫВОД СРЕДСТВ", "ℹ️ ИНФО", "🆘 ПОДДЕРЖКА", "🔙 НАЗАД", "❌ ОТМЕНА"])
async def support_msg(message: types.Message):
    if is_banned(message.from_user.id):
        return
    await notify_admins(message.bot, f"🆘 ВОПРОС ОТ @{message.from_user.username}\n\n{message.text}")
    await message.answer("✅ ОТПРАВЛЕНО!", reply_markup=main_keyboard())

# ========== ПАГИНАЦИЯ ==========
@user_router.callback_query(lambda c: c.data.startswith("history_"))
async def history_page(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[1])
    withdraws = load_withdraws()
    my = [w for w in withdraws if w["user_id"] == callback.from_user.id]
    my.reverse()
    await show_history(callback.message, my, page)
    await callback.answer()

@user_router.callback_query(lambda c: c.data == "to_main")
async def to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 ГЛАВНОЕ МЕНЮ", reply_markup=main_keyboard())
    await callback.answer()
