from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import MIN_WITHDRAW
from database import get_user, get_pending_withdrawals_count, check_consent, set_consent, add_user
from keyboards import get_main_menu, get_profile_keyboard, get_rating_keyboard
from utils import WithdrawStates, ReviewStates, SupportStates

router = Router()

# === СТАРТ ===
@router.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "нет username"
    add_user(user_id, username)
    
    if not check_consent(user_id):
        text = (
            "🔒 *Данный бот запрашивает соглашение для обработки персональных данных.*\n\n"
            "Мы чтим анонимность, но в данном боте будут обрабатываться платежи.\n\n"
            "1. Вы согласны на обработку персональных данных\n"
            "2. Вы ознакомились с правилами и условиями в этом канале: https://t.me/+ZAJelSN78aliNzIx"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен", callback_data="consent_agree")]
        ])
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await show_welcome(message)

@router.callback_query(F.data == "consent_agree")
async def consent_handler(callback: types.CallbackQuery):
    set_consent(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer("✅ Согласие получено!", reply_markup=get_main_menu())
    await callback.answer()

async def show_welcome(event):
    text = "🎉 *Добро пожаловать!*\n\nТут и идут все выплаты, для анонимности и чтобы не путаться)"
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, parse_mode="Markdown", reply_markup=get_main_menu())
        await event.answer()
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=get_main_menu())

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    await show_welcome(callback)

# === ПРОФИЛЬ ===
@router.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка", show_alert=True)
        return
    text = f"👤 *Ваш профиль*\n\n📝 Username: @{user[1]}\n💰 Баланс: {user[2]} USDT\n⏳ Заявок в ожидании: {get_pending_withdrawals_count(callback.from_user.id)}"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_profile_keyboard())
    await callback.answer()
