from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from database import get_user_by_id, is_banned, update_user, add_withdraw, load_withdraws, save_withdraws, delete_old_withdraws
from keyboards import main_keyboard, profile_keyboard, cancel_keyboard, withdraw_method_keyboard
from utils import notify_admins
from config import MIN_WITHDRAW

withdraw_router = Router()

class WithdrawState:
    amount = "withdraw_amount"
    details = "withdraw_details"

@withdraw_router.message(lambda msg: msg.text == "💰 ВЫВОД СРЕДСТВ")
async def withdraw_start(message: types.Message, state: FSMContext):
    if is_banned(message.from_user.id):
        return
    user = get_user_by_id(message.from_user.id)
    if user["balance"] < MIN_WITHDRAW:
        await message.answer(f"❌ МИНИМАЛЬНАЯ СУММА ВЫВОДА {MIN_WITHDRAW} USDT", reply_markup=profile_keyboard())
        return
    await message.answer(f"💰 ВАШ БАЛАНС: {user['balance']} USDT\n\nВВЕДИТЕ СУММУ:", reply_markup=cancel_keyboard())
    await state.set_state(WithdrawState.amount)

@withdraw_router.message(WithdrawState.amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ ОТМЕНА":
        await state.clear()
        await message.answer("❌ ОТМЕНЕНО", reply_markup=main_keyboard())
        return
    try:
        amount = float(message.text)
        user = get_user_by_id(message.from_user.id)
        if amount < MIN_WITHDRAW:
            await message.answer(f"❌ МИНИМУМ {MIN_WITHDRAW} USDT")
            return
        if amount > user["balance"]:
            await message.answer(f"❌ У ВАС {user['balance']} USDT")
            return
        await state.update_data(amount=amount)
        await message.answer("💳 ВЫБЕРИТЕ СПОСОБ:", reply_markup=withdraw_method_keyboard())
        await state.set_state(WithdrawState.details)
    except:
        await message.answer("❌ ВВЕДИТЕ ЧИСЛО")

@withdraw_router.callback_query(lambda c: c.data.startswith("withdraw_"))
async def withdraw_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    if method == "card":
        await callback.message.edit_text("💳 ВВЕДИТЕ НОМЕР КАРТЫ:")
        await state.update_data(method="БАНКОВСКАЯ КАРТА")
    elif method == "crypto":
        await callback.message.edit_text("₿ ВВЕДИТЕ ССЫЛКУ НА ОПЛАТУ ИЗ @CryptoBot:")
        await state.update_data(method="КРИПТОКОШЕЛЁК")
    else:
        await callback.message.edit_text("📞 ЗАЯВКА ОТПРАВЛЕНА АДМИНУ")
        await notify_admins(callback.bot, f"📞 ЗАПРОС СВЯЗИ ОТ @{callback.from_user.username}")
        await state.clear()
        await callback.bot.send_message(callback.from_user.id, "✅ АДМИН СВЯЖЕТСЯ", reply_markup=main_keyboard())
    await callback.answer()

@withdraw_router.message(WithdrawState.details)
async def withdraw_details(message: types.Message, state: FSMContext):
    if message.text == "❌ ОТМЕНА":
        await state.clear()
        await message.answer("❌ ОТМЕНЕНО", reply_markup=main_keyboard())
        return
    data = await state.get_data()
    withdraw = {
        "id": int(datetime.now().timestamp()),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "amount": data["amount"],
        "method": data.get("method", "НЕ УКАЗАН"),
        "details": message.text,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    add_withdraw(withdraw)
    await notify_admins(message.bot, f"💰 НОВАЯ ЗАЯВКА!\nОТ: @{message.from_user.username}\nСУММА: {data['amount']} USDT\nСПОСОБ: {data.get('method')}\nРЕКВИЗИТЫ: {message.text}")
    await state.clear()
    await message.answer("✅ ЗАЯВКА ОТПРАВЛЕНА!", reply_markup=main_keyboard())
