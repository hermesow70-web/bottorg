from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from database import add_review
from keyboards import main_menu, rating_menu, review_options_menu, anonymous_menu
from utils import notify_admins
from config import REVIEWS_CHANNEL

review_router = Router()

class ReviewState(StatesGroup):
    rating = State()
    comment = State()

@review_router.callback_query(F.data == "review")
async def review_start_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("⭐ **Оцените наш сервис:**", reply_markup=rating_menu())
    await callback.answer()

@review_router.callback_query(F.data.startswith("rate_"))
async def review_rating_callback(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    await callback.message.edit_text("💬 **Напишите комментарий или пропустите:**", reply_markup=review_options_menu())
    await callback.answer()

@review_router.callback_query(F.data == "review_write")
async def review_write_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ReviewState.comment)
    await callback.message.edit_text("✏️ **Напишите ваш комментарий:**", reply_markup=anonymous_menu())
    await callback.answer()

@review_router.callback_query(F.data == "review_skip")
async def review_skip_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await show_anonymous_options(callback.message, state)

async def show_anonymous_options(message, state: FSMContext):
    await message.edit_text("📢 **Как отправить отзыв?**", reply_markup=anonymous_menu())

@review_router.message(ReviewState.comment)
async def review_comment_cmd(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await show_anonymous_options(message, state)

@review_router.callback_query(F.data.startswith("review_"))
async def review_send_callback(callback: CallbackQuery, state: FSMContext):
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
