from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS, MIN_WITHDRAW
from database import get_user, update_balance, add_withdrawal
from keyboards import get_profile_keyboard
from utils import WithdrawStates

router = Router()

@router.callback_query(F.data == "withdraw")
async def withdraw_request(callback: types.CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if user[2] < MIN_WITHDRAW:
        await callback.message.edit_text(f"❌ Минимальная сумма вывода: {MIN_WITHDRAW} USDT\nВаш баланс: {user[2]} USDT", reply_markup=get_profile_keyboard())
        await callback.answer()
        return
    await state.set_state(WithdrawStates.waiting_amount)
    await callback.message.edit_text(f"💰 Введите сумму вывода (мин {MIN_WITHDRAW} USDT):", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Отмена", callback_data="profile")]]))
    await callback.answer()

@router.message(WithdrawStates.waiting_amount)
async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < MIN_WITHDRAW:
            await message.answer(f"❌ Минимальная сумма {MIN_WITHDRAW} USDT")
            return
        user = get_user(message.from_user.id)
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

@router.callback_query(WithdrawStates.waiting_method, F.data.startswith("method_"))
async def withdraw_method_handler(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    await state.update_data(method=method)
    await state.set_state(WithdrawStates.waiting_details)
    text = "💳 Введите номер карты (не СПБ):" if method == "card" else "🤖 Пришлите ссылку на многоразовый счёт Crypto bot:"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Отмена", callback_data="profile")]]))
    await callback.answer()

@router.message(WithdrawStates.waiting_details)
async def handle_withdraw_details(message: types.Message, state: FSMContext):
    data = await state.update_data(details=message.text)
    text = f"✅ *Проверьте данные:*\n\n💰 Сумма: {data['amount']} USDT\n💳 Способ: {data['method']}\n📝 Реквизиты: {data['details']}\n\nВсё верно?"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить заявку", callback_data="submit_withdraw")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="profile")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    await state.set_state(WithdrawStates.waiting_confirm)

@router.callback_query(WithdrawStates.waiting_confirm, F.data == "submit_withdraw")
async def submit_withdraw(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    update_balance(callback.from_user.id, -data['amount'])
    add_withdrawal(callback.from_user.id, data['amount'], data['method'], data['details'])
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(admin_id, f"🆕 *Новая заявка на вывод*\n\n👤 User ID: {callback.from_user.id}\n💰 Сумма: {data['amount']} USDT\n💳 Способ: {data['method']}\n📝 Реквизиты: {data['details']}")
        except:
            pass
    await callback.message.edit_text("✅ Ваша заявка подана! Ожидайте решения администратора.", reply_markup=get_profile_keyboard())
    await state.clear()
    await callback.answer()
