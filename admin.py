from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from database import (
    get_user_by_username, ban_user, unban_user, update_balance,
    get_user, load_withdraws, update_withdraw_status, add_to_withdrawn,
    notify_admins, notify_user
)
from keyboards import admin_menu, admin_ban_menu, admin_balance_menu, back_menu, main_menu, withdraw_action_menu
from config import ADMIN_IDS

admin_router = Router()

class AdminState(StatesGroup):
    username = State()
    amount = State()
    action = State()
    reply_user_id = State()

@admin_router.message(lambda msg: msg.text and msg.from_user.id in ADMIN_IDS)
async def admin_text_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("reply_user_id"):
        user_id = data.get("reply_user_id")
        await notify_user(message.bot, user_id, f"💬 **Ответ администратора:**\n\n{message.text}")
        await message.answer("✅ Ответ отправлен!")
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_menu())

@admin_router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    await callback.message.edit_text("👑 **Админ-панель**", reply_markup=admin_menu())
    await callback.answer()

@admin_router.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    await callback.message.edit_text("👑 **Админ-панель**", reply_markup=admin_menu())
    await callback.answer()

@admin_router.callback_query(F.data == "admin_ban")
async def admin_ban_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    await callback.message.edit_text("👥 **Управление баном**", reply_markup=admin_ban_menu())
    await callback.answer()

@admin_router.callback_query(F.data == "admin_balance")
async def admin_balance_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    await callback.message.edit_text("💰 **Управление балансом**", reply_markup=admin_balance_menu())
    await callback.answer()

@admin_router.callback_query(F.data == "admin_requests")
async def admin_requests_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    withdraws = load_withdraws()
    pending = [w for w in withdraws if w["status"] == "pending"]
    
    if not pending:
        await callback.message.edit_text("📭 **Нет активных заявок**", reply_markup=admin_menu())
        await callback.answer()
        return
    
    for w in pending:
        text = (
            f"💰 **Заявка на вывод**\n\n"
            f"👤 От: @{w['username']}\n"
            f"💵 Сумма: {w['amount']} USDT\n"
            f"💳 Способ: {w['method']}\n"
            f"📝 Реквизиты:\n{w['details']}\n"
            f"📅 {w['created_at'][:19]}"
        )
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=withdraw_action_menu(w["id"]))
    
    await callback.message.delete()
    await callback.answer()

@admin_router.callback_query(F.data == "ban_user")
async def ban_user_start_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    await state.update_data(action="ban")
    await state.set_state(AdminState.username)
    await callback.message.edit_text("🔨 **Введите username пользователя (без @):**", reply_markup=back_menu())
    await callback.answer()

@admin_router.callback_query(F.data == "unban_user")
async def unban_user_start_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    await state.update_data(action="unban")
    await state.set_state(AdminState.username)
    await callback.message.edit_text("🔓 **Введите username пользователя (без @):**", reply_markup=back_menu())
    await callback.answer()

@admin_router.callback_query(F.data == "balance_add")
async def balance_add_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    await state.update_data(action="add")
    await state.set_state(AdminState.username)
    await callback.message.edit_text("➕ **Введите username пользователя (без @):**", reply_markup=back_menu())
    await callback.answer()

@admin_router.callback_query(F.data == "balance_subtract")
async def balance_subtract_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    await state.update_data(action="subtract")
    await state.set_state(AdminState.username)
    await callback.message.edit_text("➖ **Введите username пользователя (без @):**", reply_markup=back_menu())
    await callback.answer()

@admin_router.callback_query(F.data == "balance_reset")
async def balance_reset_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    await state.update_data(action="reset")
    await state.set_state(AdminState.username)
    await callback.message.edit_text("🔄 **Введите username пользователя (без @):**", reply_markup=back_menu())
    await callback.answer()

@admin_router.message(AdminState.username)
async def admin_username_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("action")
    username = message.text.strip().replace("@", "")
    
    user = get_user_by_username(username)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    if action == "ban":
        ban_user(user["id"])
        await message.answer(f"✅ **Пользователь @{user['username']} забанен**", parse_mode="Markdown")
        await notify_user(message.bot, user["id"], "❌ **Вы были забанены администратором.**")
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_menu())
        
    elif action == "unban":
        unban_user(user["id"])
        await message.answer(f"✅ **Пользователь @{user['username']} разбанен**", parse_mode="Markdown")
        await notify_user(message.bot, user["id"], "✅ **Вы были разбанены.**")
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_menu())
        
    elif action == "reset":
        old_balance = user["balance"]
        update_balance(user["id"], 0)
        await message.answer(f"✅ **Баланс обнулён**\n\n👤 @{user['username']}\n📊 {old_balance} → 0 USDT", parse_mode="Markdown")
        await notify_user(message.bot, user["id"], f"🔄 **Ваш баланс обнулён!**\nБыло: {old_balance} USDT\nСтало: 0 USDT")
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_menu())
        
    elif action in ["add", "subtract"]:
        await state.update_data(user_id=user["id"], username=user["username"])
        action_text = "начислить" if action == "add" else "списать"
        await message.answer(f"👤 @{user['username']}\n💰 Баланс: {user['balance']} USDT\n\n💵 **Введите сумму для {action_text} (USDT):**", parse_mode="Markdown")
        await state.set_state(AdminState.amount)

@admin_router.message(AdminState.amount)
async def admin_amount_handler(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0")
            return
        
        data = await state.get_data()
        user_id = data.get("user_id")
        username = data.get("username")
        action = data.get("action")
        user = get_user(user_id)
        
        if action == "add":
            new_balance = user["balance"] + amount
            update_balance(user_id, new_balance)
            await message.answer(f"✅ **Начислено {amount} USDT**\n\n👤 @{username}\n📊 {user['balance'] - amount} → {new_balance} USDT", parse_mode="Markdown")
            await notify_user(message.bot, user_id, f"➕ **Начислено {amount} USDT!**\n💰 Новый баланс: {new_balance} USDT")
        else:
            if amount > user["balance"]:
                await message.answer(f"❌ Недостаточно средств! Баланс: {user['balance']} USDT")
                return
            new_balance = user["balance"] - amount
            update_balance(user_id, new_balance)
            await message.answer(f"✅ **Списано {amount} USDT**\n\n👤 @{username}\n📊 {user['balance'] + amount} → {new_balance} USDT", parse_mode="Markdown")
            await notify_user(message.bot, user_id, f"➖ **Списано {amount} USDT**\n💰 Новый баланс: {new_balance} USDT")
        
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_menu())
    except:
        await message.answer("❌ Введите число")

@admin_router.callback_query(F.data.startswith("approve_"))
async def approve_withdraw_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    wid = int(callback.data.split("_")[1])
    w = update_withdraw_status(wid, "approved")
    
    if w:
        user = get_user(w["user_id"])
        if user:
            new_balance = user["balance"] - w["amount"]
            update_balance(w["user_id"], new_balance)
            add_to_withdrawn(w["user_id"], w["amount"])
            await notify_user(callback.bot, w["user_id"], f"✅ **Заявка одобрена!**\n💵 {w['amount']} USDT\n💰 Новый баланс: {new_balance} USDT")
        
        await callback.message.edit_text(f"✅ Одобрено\n{callback.message.text}")
    
    await callback.answer()

@admin_router.callback_query(F.data.startswith("reject_"))
async def reject_withdraw_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    wid = int(callback.data.split("_")[1])
    w = update_withdraw_status(wid, "rejected")
    
    if w:
        await notify_user(callback.bot, w["user_id"], f"❌ **Заявка отклонена!**\n💵 {w['amount']} USDT\n📞 Обратитесь в поддержку")
        await callback.message.edit_text(f"❌ Отклонено\n{callback.message.text}")
    
    await callback.answer()

@admin_router.callback_query(F.data.startswith("reply_"))
async def reply_withdraw_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    wid = int(callback.data.split("_")[1])
    withdraws = load_withdraws()
    for w in withdraws:
        if w["id"] == wid:
            await state.update_data(reply_user_id=w["user_id"])
            await callback.message.answer("💬 **Введите ответ пользователю:**", reply_markup=back_menu())
            break
    
    await callback.answer()
