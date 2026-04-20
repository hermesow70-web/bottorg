from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS, MIN_WITHDRAW
from database import get_user, update_balance, add_withdrawal, is_banned
from keyboards import get_profile_keyboard
from util import WithdrawStates

router = Router()

async def check_ban(user_id):
    user = get_user(user_id)
    if user and user[3] == 1:
        return True
    return False

@router.callback_query(F.data == "withdraw")
async def withdraw_request(callback: types.CallbackQuery, state: FSMContext):
    if await check_ban(callback.from_user.id):
        await callback.message.edit_text("❌ Вы забанены! Обратитесь к администратору.")
        await callback.answer()
        return
    
    user = get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("❌ Ошибка! Попробуйте позже.")
        await callback.answer()
        return
        
    if user[2] < MIN_WITHDRAW:
        await callback.message.edit_text(f"❌ Минимальная сумма вывода: {MIN_WITHDRAW} USDT\nВаш баланс: {user[2]} USDT", reply_markup=get_profile_keyboard())
        await callback.answer()
        return
    await state.set_state(WithdrawStates.waiting_amount)
    await callback.message.edit_text(f"💰 Введите сумму вывода (мин {MIN_WITHDRAW} USDT):", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Отмена", callback_data="profile")]]))
    await callback.answer()

@router.message(WithdrawStates.waiting_amount)
async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    if await check_ban(message.from_user.id):
        await message.answer("❌ Вы забанены! Обратитесь к администратору.")
        return
        
    try:
        amount = float(message.text)
        if amount < MIN_WITHDRAW:
            await message.answer(f"❌ Минимальная сумма {MIN_WITHDRAW} USDT")
            return
        user = get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Ошибка! Попробуйте позже.")
            return
        if amount > user[2]:
            await message.answer(f"❌ Недостаточно средств. Баланс: {user[2]} USDT")
            return
        await state.update_data(amount=amount)
        await state.set_state(WithdrawStates.waiting_method)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Карта (не СПБ)", callback_data="method_card")],
            [InlineKeyboardButton(text="🤖 Crypto bot", callback_data="method_crypto")],
            [InlineKeyboardButton(text="🏠 Отмена", callback_data="profile")]
        ])
        await message.answer("Выберите способ вывода:", reply_markup=keyboard)
    except ValueError:
        await message.answer("❌ Введите число!")

# ... остальные обработчики с добавлением проверки бана
