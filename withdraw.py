from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user_by_id, is_banned, update_user, add_withdraw
from keyboards import main_keyboard, profile_keyboard, cancel_keyboard, withdraw_method_keyboard
from utils import notify_admins
from config import MIN_WITHDRAW

withdraw_router = Router()

class WithdrawState(StatesGroup):
    amount = State()
    details = State()

@withdraw_router.message(F.text == "💰 Вывод средств")
async def withdraw_start_cmd(message: types.Message, state: FSMContext):
    if is_banned(message.from_user.id):
        return
    user = get_user_by_id(message.from_user.id)
    if user["balance"] < MIN_WITHDRAW:
        await message.answer(f"❌ Минимальная сумма вывода {MIN_WITHDRAW} USDT", reply_markup=profile_keyboard())
        return
    await message.answer(f"💰 Ваш баланс: {user['balance']} USDT\n\nВведите сумму:", reply_markup=cancel_keyboard())
    await state.set_state(WithdrawState.amount)

@withdraw_router.message(WithdrawState.amount)
async def withdraw_amount_cmd(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=main_keyboard())
        return
    try:
        amount = float(message.text)
        user = get_user_by_id(message.from_user.id)
        if amount < MIN_WITHDRAW:
            await message.answer(f"❌ Минимум {MIN_WITHDRAW} USDT")
            return
        if amount > user["balance"]:
            await message.answer(f"❌ У вас {user['balance']} USDT")
            return
        await state.update_data(amount=amount)
        await message.answer("💳 Выберите способ:", reply_markup=withdraw_method_keyboard())
        await state.set_state(WithdrawState.details)
    except:
        await message.answer("❌ Введите число")

@withdraw_router.callback_query(lambda c: c.data.startswith("withdraw_"))
async def withdraw_method_callback(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    if method == "card":
        await callback.message.edit_text("💳 Введите номер карты:")
        await state.update_data(method="Банковская карта")
    elif method == "crypto":
        await callback.message.edit_text("₿ Введите ссылку на оплату из @CryptoBot:")
        await state.update_data(method="Криптокошелёк")
    else:
        await callback.message.edit_text("📞 Заявка отправлена админу")
        await notify_admins(callback.bot, f"📞 Запрос связи от @{callback.from_user.username}")
        await state.clear()
        await callback.bot.send_message(callback.from_user.id, "✅ Админ свяжется", reply_markup=main_keyboard())
    await callback.answer()

@withdraw_router.message(WithdrawState.details)
async def withdraw_details_cmd(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=main_keyboard())
        return
    data = await state.get_data()
    withdraw = {
        "id": int(datetime.now().timestamp()),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "amount": data["amount"],
        "method": data.get("method", "Не указан"),
        "details": message.text,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    add_withdraw(withdraw)
    await notify_admins(
        message.bot,
        f"💰 **Новая заявка!**\n\n"
        f"От: @{message.from_user.username}\n"
        f"Сумма: {data['amount']} USDT\n"
        f"Способ: {data.get('method')}\n"
        f"Реквизиты: {message.text}"
    )
    await state.clear()
    await message.answer("✅ Заявка отправлена!", reply_markup=main_keyboard())
