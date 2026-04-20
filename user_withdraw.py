from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from database import get_user, add_withdraw
from keyboards import main_menu, profile_menu, withdraw_method_menu, withdraw_card_type_menu, back_menu, withdraw_action_menu
from utils import notify_admins
from config import MIN_WITHDRAW

withdraw_router = Router()

class WithdrawState(StatesGroup):
    amount = State()
    card_type = State()
    phone = State()
    bank = State()
    name = State()
    crypto_link = State()

@withdraw_router.callback_query(F.data == "withdraw_start")
async def withdraw_start_callback(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if user["balance"] < MIN_WITHDRAW:
        await callback.answer(f"Минимальная сумма {MIN_WITHDRAW} USDT", show_alert=True)
        return
    
    await state.set_state(WithdrawState.amount)
    await callback.message.edit_text(
        f"💸 **Введите сумму вывода (от {MIN_WITHDRAW} USDT):**",
        parse_mode="Markdown",
        reply_markup=back_menu()
    )
    await callback.answer()

@withdraw_router.message(WithdrawState.amount)
async def withdraw_amount_cmd(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < MIN_WITHDRAW:
            await message.answer(f"❌ Сумма должна быть не менее {MIN_WITHDRAW} USDT\nВведите другую сумму:")
            return
        
        user = get_user(message.from_user.id)
        if amount > user["balance"]:
            await message.answer(f"❌ У вас {user['balance']} USDT\nВведите сумму не больше баланса:")
            return
        
        await state.update_data(amount=amount)
        await message.answer("💳 **Выберите способ вывода:**", reply_markup=withdraw_method_menu())
    except:
        await message.answer("❌ Введите число")

@withdraw_router.callback_query(F.data == "method_card")
async def withdraw_card_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(method="card")
    await callback.message.edit_text("💳 **Выберите тип перевода:**", reply_markup=withdraw_card_type_menu())
    await callback.answer()

@withdraw_router.callback_query(F.data == "method_crypto")
async def withdraw_crypto_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(method="crypto")
    await state.set_state(WithdrawState.crypto_link)
    await callback.message.edit_text(
        "🤖 **Отправьте ссылку на счёт из @CryptoBot**\n\n"
        "1. Перейдите в @CryptoBot\n"
        "2. Создайте счёт на оплату\n"
        "3. Пришлите ссылку сюда:",
        parse_mode="Markdown",
        reply_markup=back_menu()
    )
    await callback.answer()

@withdraw_router.callback_query(F.data == "card_sbp")
async def card_sbp_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(card_type="sbp")
    await state.set_state(WithdrawState.phone)
    await callback.message.edit_text("📱 **Введите номер телефона (привязанный к банку):**", reply_markup=back_menu())
    await callback.answer()

@withdraw_router.callback_query(F.data == "card_number")
async def card_number_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(card_type="card_number")
    await state.set_state(WithdrawState.phone)
    await callback.message.edit_text("💳 **Введите номер карты (16 цифр):**", reply_markup=back_menu())
    await callback.answer()

@withdraw_router.message(WithdrawState.phone)
async def withdraw_phone_cmd(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("card_type") == "sbp":
        await state.update_data(phone=message.text)
        await message.answer("🏦 **Введите название вашего банка:**")
        await state.set_state(WithdrawState.bank)
    else:
        await state.update_data(card_number=message.text)
        await message.answer("👤 **Введите имя получателя (как на карте):**")
        await state.set_state(WithdrawState.name)

@withdraw_router.message(WithdrawState.bank)
async def withdraw_bank_cmd(message: Message, state: FSMContext):
    await state.update_data(bank=message.text)
    await message.answer("👤 **Введите имя получателя:**")
    await state.set_state(WithdrawState.name)

@withdraw_router.message(WithdrawState.name)
async def withdraw_name_cmd(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await finish_withdraw(message, state)

@withdraw_router.message(WithdrawState.crypto_link)
async def withdraw_crypto_link_cmd(message: Message, state: FSMContext):
    await state.update_data(crypto_link=message.text)
    await finish_withdraw(message, state)

async def finish_withdraw(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data["amount"]
    method = data["method"]
    
    if method == "card":
        if data.get("card_type") == "sbp":
            details = f"СБП\nТелефон: {data['phone']}\nБанк: {data['bank']}\nИмя: {data['name']}"
        else:
            details = f"Номер карты: {data['card_number']}\nИмя: {data['name']}"
    else:
        details = f"Crypto Bot ссылка: {data['crypto_link']}"
    
    withdraw = {
        "id": int(datetime.now().timestamp()),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "amount": amount,
        "method": method,
        "details": details,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    add_withdraw(withdraw)
    
    await notify_admins(
        message.bot,
        f"💰 **Новая заявка на вывод!**\n\n"
        f"👤 От: @{message.from_user.username}\n"
        f"💵 Сумма: {amount} USDT\n"
        f"💳 Способ: {method}\n"
        f"📝 Реквизиты:\n{details}",
        withdraw_action_menu(withdraw["id"])
    )
    
    await message.answer(
        f"✅ **Заявка на вывод {amount} USDT отправлена!**\n\n⏳ Статус: **В ожидании**",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await state.clear()
