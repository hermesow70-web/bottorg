from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import REVIEWS_CHANNEL, ADMIN_IDS
from database import save_review, save_appeal
from keyboards import get_main_menu, get_rating_keyboard
from util import ReviewStates, SupportStates

router = Router()

@router.callback_query(F.data == "review")
async def review_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ReviewStates.waiting_rating)
    await callback.message.edit_text("⭐ *Оцените наш сервис от 1 до 5 звёзд:*", parse_mode="Markdown", reply_markup=get_rating_keyboard())
    await callback.answer()

@router.callback_query(ReviewStates.waiting_rating, F.data.startswith("rating_"))
async def rating_handler(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    if rating <= 3:
        await state.set_state(ReviewStates.waiting_comment)
        await callback.message.edit_text("😔 Пожалуйста, напишите, что вам не понравилось, мы обязательно исправим:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⏭️ Пропустить", callback_data="review_skip")]]))
    else:
        await callback.message.edit_text("🎉 Спасибо за ваш отзыв! Хотите добавить комментарий?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Добавить комментарий", callback_data="review_add_comment")],
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="review_skip")]
        ]))
    await callback.answer()

@router.callback_query(F.data == "review_add_comment")
async def review_add_comment(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ReviewStates.waiting_comment)
    await callback.message.edit_text("📝 Напишите ваш комментарий:")
    await callback.answer()

@router.callback_query(F.data == "review_skip")
async def review_skip(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(comment="")
    await ask_anonymous(callback, state)

@router.message(ReviewStates.waiting_comment)
async def handle_review_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await ask_anonymous(message, state)

async def ask_anonymous(event, state: FSMContext):
    text = "🕵️ Отправить отзыв анонимно?"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕵️ Анонимно", callback_data="review_anon_yes")],
        [InlineKeyboardButton(text="👤 С именем", callback_data="review_anon_no")]
    ])
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard)
    await state.set_state(ReviewStates.waiting_anonymous)

@router.callback_query(ReviewStates.waiting_anonymous, F.data.startswith("review_anon_"))
async def submit_review(callback: types.CallbackQuery, state: FSMContext):
    anonymous = callback.data == "review_anon_yes"
    data = await state.get_data()
    user_id = callback.from_user.id
    username = callback.from_user.username or "нет username"
    rating = data.get('rating')
    comment = data.get('comment', '')
    save_review(user_id, rating, comment, anonymous)
    review_text = f"⭐ Оценка: {rating}/5\n💬 Комментарий: {comment}\n{'🕵️ Анонимно' if anonymous else f'👤 От: @{username}'}"
    try:
        await callback.bot.send_message(REVIEWS_CHANNEL, review_text)
    except:
        pass
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(admin_id, f"📝 Новый отзыв!\n{review_text}")
        except:
            pass
    await callback.message.edit_text("✅ Спасибо за ваш отзыв!", reply_markup=get_main_menu())
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "support")
async def support_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_message)
    await callback.message.edit_text("🆘 Напишите ваше обращение, администратор обязательно его рассмотрит:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]]))
    await callback.answer()

@router.message(SupportStates.waiting_message)
async def handle_support_message(message: types.Message, state: FSMContext):
    save_appeal(message.from_user.id, message.text)
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, f"🆘 *Новое обращение*\n\n👤 User ID: {message.from_user.id}\n💬 Сообщение: {message.text}")
        except:
            pass
    await message.answer("✅ Ваше обращение отправлено! Администратор свяжется с вами.", reply_markup=get_main_menu())
    await state.clear()
