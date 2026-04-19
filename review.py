from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from database import get_user_by_id, is_banned, update_user, add_review
from keyboards import main_keyboard, cancel_keyboard, rating_keyboard, review_actions_keyboard, anonymous_keyboard
from utils import notify_admins
from config import REVIEWS_CHANNEL

review_router = Router()

class ReviewState:
    rating = "review_rating"
    comment = "review_comment"

@review_router.message(lambda msg: msg.text == "⭐ ОСТАВИТЬ ОТЗЫВ")
async def review_start(message: types.Message, state: FSMContext):
    if is_banned(message.from_user.id):
        return
    await message.answer("⭐ ОЦЕНИТЕ НАС:", reply_markup=rating_keyboard())
    await state.set_state(ReviewState.rating)

@review_router.callback_query(lambda c: c.data.startswith("rating_"))
async def review_rating(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    await callback.message.edit_text("💬 НАПИШИТЕ КОММЕНТАРИЙ ИЛИ ПРОПУСТИТЕ:", reply_markup=review_actions_keyboard())
    await callback.answer()

@review_router.callback_query(lambda c: c.data == "review_write")
async def review_write(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ НАПИШИТЕ ВАШ КОММЕНТАРИЙ:", reply_markup=cancel_keyboard())
    await state.set_state(ReviewState.comment)
    await callback.answer()

@review_router.callback_query(lambda c: c.data == "review_skip")
async def review_skip(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await callback.message.edit_text("📢 ОТПРАВИТЬ АНОНИМНО ИЛИ С ИМЕНЕМ?", reply_markup=anonymous_keyboard())
    await callback.answer()

@review_router.message(ReviewState.comment)
async def review_comment(message: types.Message, state: FSMContext):
    if message.text == "❌ ОТМЕНА":
        await state.clear()
        await message.answer("❌ ОТМЕНЕНО", reply_markup=main_keyboard())
        return
    await state.update_data(comment=message.text)
    await message.answer("📢 ОТПРАВИТЬ АНОНИМНО ИЛИ С ИМЕНЕМ?", reply_markup=anonymous_keyboard())

@review_router.callback_query(lambda c: c.data in ["review_named", "review_anonymous", "review_cancel"])
async def review_send(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "review_cancel":
        await state.clear()
        await callback.message.edit_text("❌ ОТМЕНЕНО", reply_markup=main_keyboard())
        await callback.answer()
        return
    
    data = await state.get_data()
    is_anon = callback.data == "review_anonymous"
    review = {
        "id": int(datetime.now().timestamp()),
        "user_id": None if is_anon else callback.from_user.id,
        "username": None if is_anon else callback.from_user.username,
        "rating": data["rating"],
        "comment": data.get("comment"),
        "is_anonymous": is_anon,
        "created_at": datetime.now().isoformat()
    }
    add_review(review)
    
    user = get_user_by_id(callback.from_user.id)
    new_count = user.get("rating_count", 0) + 1
    new_score = user.get("rating_score", 0) + data["rating"]
    update_user(callback.from_user.id, {"rating_count": new_count, "rating_score": new_score})
    
    stars = "⭐" * data["rating"]
    name = "АНОНИМ" if is_anon else f"@{callback.from_user.username}"
    comment_text = data.get("comment", "БЕЗ КОММЕНТАРИЯ")
    
    try:
        await callback.bot.send_message(
            REVIEWS_CHANNEL,
            f"⭐ **НОВЫЙ ОТЗЫВ!**\n\n👤 {name}\n⭐ {data['rating']}/5 {stars}\n💬 {comment_text}\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await notify_admins(callback.bot, f"⭐ ОТЗЫВ ОТ {name}\nОЦЕНКА: {data['rating']}/5\nКОММЕНТАРИЙ: {comment_text}")
    await state.clear()
    await callback.message.edit_text("✅ СПАСИБО ЗА ОТЗЫВ!", reply_markup=main_keyboard())
    await callback.answer()
