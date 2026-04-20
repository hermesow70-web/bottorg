from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    load_users, save_users, get_user_by_username, update_balance, get_user,
    load_withdraws, update_withdraw_status, add_to_withdrawn,
    ban_user, unban_user, is_banned
)
from keyboards import (
    admin_keyboard, balance_admin_keyboard, back_keyboard,
    ban_keyboard, main_keyboard, withdraw_action_keyboard
)
from config import ADMIN_IDS

admin_router = Router()

class AdminBalanceState(StatesGroup):
    username = State()
    amount = State()
    action = State()

class AdminBanState(StatesGroup):
    username = State()

class AdminReplyState(StatesGroup):
    user_id = State()
    message = State()

async def notify_admins(bot, text):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown")
        except:
            pass

async def notify_user(bot, user_id, text):
    try:
        await bot.send_message(user_id, text, parse_mode="Markdown")
    except:
        pass

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ НЕТ ДОСТУПА")
        return
    await message.answer("👑 **АДМИН-ПАНЕЛЬ**", reply_markup=admin_keyboard(), parse_mode="Markdown")

@admin_router.message(F.text == "◀️ НАЗАД")
async def back_to_admin(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👑 **АДМИН-ПАНЕЛЬ**", reply_markup=admin_keyboard(), parse_mode="Markdown")

@admin_router.message(F.text == "👥 БАН/РАЗБАН")
async def ban_menu(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("👥 **УПРАВЛЕНИЕ БАНОМ**", reply_markup=ban_keyboard(), parse_mode="Markdown")

@admin_router.message(F.text == "🔨 ЗАБАНИТЬ")
async def ban_user_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("ВВЕДИТЕ **USERNAME** ПОЛЬЗОВАТЕЛЯ (БЕЗ @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBanState.username)

@admin_router.message(AdminBanState.username)
async def ban_user_execute(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await ban_menu(message)
        return
    
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        return
    
    ban_user(user["id"])
    
    await message.answer(f"✅ **ПОЛЬЗОВАТЕЛЬ @{user['username']} ЗАБАНЕН**", parse_mode="Markdown", reply_markup=admin_keyboard())
    await notify_admins(message.bot, f"🔨 АДМИН ЗАБАНИЛ @{user['username']}")
    await notify_user(message.bot, user["id"], "❌ **ВЫ БЫЛИ ЗАБАНЕНЫ АДМИНИСТРАТОРОМ.**")
    await state.clear()

@admin_router.message(F.text == "🔓 РАЗБАНИТЬ")
async def unban_user_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("ВВЕДИТЕ **USERNAME** ПОЛЬЗОВАТЕЛЯ (БЕЗ @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBanState.username)

@admin_router.message(AdminBanState.username)
async def unban_user_execute(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await ban_menu(message)
        return
    
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        return
    
    unban_user(user["id"])
    
    await message.answer(f"✅ **ПОЛЬЗОВАТЕЛЬ @{user['username']} РАЗБАНЕН**", parse_mode="Markdown", reply_markup=admin_keyboard())
    await notify_admins(message.bot, f"🔓 АДМИН РАЗБАНИЛ @{user['username']}")
    await notify_user(message.bot, user["id"], "✅ **ВЫ БЫЛИ РАЗБАНЕНЫ.**")
    await state.clear()

@admin_router.message(F.text == "📋 ЗАЯВКИ")
async def list_withdraws(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    withdraws = load_withdraws()
    pending = [w for w in withdraws if w["status"] == "pending"]
    
    if not pending:
        await message.answer("📭 **НЕТ АКТИВНЫХ ЗАЯВОК НА ВЫВОД**", parse_mode="Markdown", reply_markup=admin_keyboard())
        return
    
    for w in pending:
        text = (
            f"💰 **ЗАЯВКА НА ВЫВОД**\n\n"
            f"👤 ОТ: @{w['username']}\n"
            f"💵 СУММА: {w['amount']} USDT\n"
            f"💳 СПОСОБ: {w['method']}\n"
            f"📝 РЕКВИЗИТЫ:\n{w['details']}\n"
            f"📅 ДАТА: {w['created_at'][:19]}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=withdraw_action_keyboard(w["id"]))

@admin_router.callback_query(lambda c: c.data.startswith("approve_"))
async def approve_withdraw(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("НЕТ ДОСТУПА")
        return
    
    wid = int(callback.data.split("_")[1])
    w = update_withdraw_status(wid, "approved")
    
    if w:
        user = get_user(w["user_id"])
        if user:
            new_balance = user["balance"] - w["amount"]
            update_balance(w["user_id"], new_balance)
            add_to_withdrawn(w["user_id"], w["amount"])
            
            await notify_user(
                callback.bot,
                w["user_id"],
                f"✅ **ВАША ЗАЯВКА НА ВЫВОД ОДОБРЕНА!**\n\n"
                f"💵 СУММА: {w['amount']} USDT\n"
                f"💰 НОВЫЙ БАЛАНС: {new_balance} USDT"
            )
        
        await notify_admins(callback.bot, f"✅ АДМИН ОДОБРИЛ ЗАЯВКУ @{w['username']} НА {w['amount']} USDT")
        await callback.message.edit_text(f"✅ ОДОБРЕНО\n{callback.message.text}")
    
    await callback.answer()

@admin_router.callback_query(lambda c: c.data.startswith("reject_"))
async def reject_withdraw(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("НЕТ ДОСТУПА")
        return
    
    wid = int(callback.data.split("_")[1])
    w = update_withdraw_status(wid, "rejected")
    
    if w:
        await notify_user(
            callback.bot,
            w["user_id"],
            f"❌ **ВАША ЗАЯВКА НА ВЫВОД ОТКЛОНЕНА!**\n\n"
            f"💵 СУММА: {w['amount']} USDT\n\n"
            f"📞 ОБРАТИТЕСЬ В ПОДДЕРЖКУ ДЛЯ УТОЧНЕНИЯ ПРИЧИНЫ."
        )
        
        await notify_admins(callback.bot, f"❌ АДМИН ОТКЛОНИЛ ЗАЯВКУ @{w['username']} НА {w['amount']} USDT")
        await callback.message.edit_text(f"❌ ОТКЛОНЕНО\n{callback.message.text}")
    
    await callback.answer()

@admin_router.callback_query(lambda c: c.data.startswith("reply_"))
async def reply_to_withdraw(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("НЕТ ДОСТУПА")
        return
    
    wid = int(callback.data.split("_")[1])
    withdraws = load_withdraws()
    w = None
    for item in withdraws:
        if item["id"] == wid:
            w = item
            break
    
    if w:
        await state.update_data(user_id=w["user_id"])
        await callback.message.answer(
            "💬 **ВВЕДИТЕ ОТВЕТ ПОЛЬЗОВАТЕЛЮ:**\n\n"
            "СООБЩЕНИЕ БУДЕТ ОТПРАВЛЕНО АНОНИМНО ОТ БОТА.",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(AdminReplyState.message)
    
    await callback.answer()

@admin_router.message(AdminReplyState.message)
async def send_reply(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await list_withdraws(message)
        return
    
    data = await state.get_data()
    user_id = data.get("user_id")
    
    await notify_user(
        message.bot,
        user_id,
        f"💬 **ОТВЕТ АДМИНИСТРАТОРА НА ВАШУ ЗАЯВКУ:**\n\n{message.text}"
    )
    
    await message.answer("✅ **ОТВЕТ ОТПРАВЛЕН ПОЛЬЗОВАТЕЛЮ!**", reply_markup=admin_keyboard())
    await state.clear()

@admin_router.message(F.text == "💰 БАЛАНС")
async def balance_admin_menu(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("💰 **УПРАВЛЕНИЕ БАЛАНСОМ**", reply_markup=balance_admin_keyboard(), parse_mode="Markdown")

@admin_router.message(F.text == "➕ НАЧИСЛИТЬ")
async def add_balance_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(action="add")
    await message.answer("ВВЕДИТЕ **USERNAME** ПОЛЬЗОВАТЕЛЯ (БЕЗ @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBalanceState.username)

@admin_router.message(F.text == "➖ СПИСАТЬ")
async def subtract_balance_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(action="subtract")
    await message.answer("ВВЕДИТЕ **USERNAME** ПОЛЬЗОВАТЕЛЯ (БЕЗ @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBalanceState.username)

@admin_router.message(F.text == "🔄 ОБНУЛИТЬ")
async def reset_balance_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(action="reset")
    await message.answer("ВВЕДИТЕ **USERNAME** ПОЛЬЗОВАТЕЛЯ (БЕЗ @):", reply_markup=back_keyboard(), parse_mode="Markdown")
    await state.set_state(AdminBalanceState.username)

@admin_router.message(AdminBalanceState.username)
async def balance_get_user(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await balance_admin_menu(message)
        return
    
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        return
    
    await state.update_data(username=message.text, user_id=user["id"])
    data = await state.get_data()
    action = data.get("action")
    
    if action == "reset":
        old_balance = user["balance"]
        update_balance(user["id"], 0)
        
        await message.answer(
            f"✅ **БАЛАНС ОБНУЛЁН**\n\n"
            f"👤 ПОЛЬЗОВАТЕЛЬ: @{user['username']}\n"
            f"📊 СТАРЫЙ БАЛАНС: {old_balance} USDT\n"
            f"📊 НОВЫЙ БАЛАНС: 0 USDT",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        
        await notify_admins(message.bot, f"🔄 АДМИН ОБНУЛИЛ БАЛАНС @{user['username']} ({old_balance} → 0 USDT)")
        await notify_user(message.bot, user["id"], f"🔄 **ВАШ БАЛАНС ОБНУЛЁН!**\n\nБЫЛО: {old_balance} USDT\nСТАЛО: 0 USDT")
        await state.clear()
    
    elif action in ["add", "subtract"]:
        action_text = "НАЧИСЛИТЬ" if action == "add" else "СПИСАТЬ"
        await message.answer(
            f"👤 ПОЛЬЗОВАТЕЛЬ: @{user['username']}\n"
            f"💰 ТЕКУЩИЙ БАЛАНС: {user['balance']} USDT\n\n"
            f"💵 ВВЕДИТЕ СУММУ ДЛЯ **{action_text}** (USDT):",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        await state.set_state(AdminBalanceState.amount)

@admin_router.message(AdminBalanceState.amount)
async def balance_amount(message: types.Message, state: FSMContext):
    if message.text == "◀️ НАЗАД":
        await state.clear()
        await balance_admin_menu(message)
        return
    
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("❌ СУММА ДОЛЖНА БЫТЬ БОЛЬШЕ 0")
            return
        
        data = await state.get_data()
        user_id = data.get("user_id")
        username = data.get("username")
        action = data.get("action")
        user = get_user(user_id)
        
        if action == "add":
            new_balance = user["balance"] + amount
            update_balance(user_id, new_balance)
            
            await message.answer(
                f"✅ **НАЧИСЛЕНО {amount} USDT**\n\n"
                f"👤 ПОЛЬЗОВАТЕЛЬ: @{username}\n"
                f"📊 СТАРЫЙ БАЛАНС: {user['balance'] - amount} USDT\n"
                f"📊 НОВЫЙ БАЛАНС: {new_balance} USDT",
                parse_mode="Markdown",
                reply_markup=admin_keyboard()
            )
            
            await notify_admins(message.bot, f"➕ АДМИН НАЧИСЛИЛ {amount} USDT @{username}")
            await notify_user(message.bot, user_id, f"➕ **ВАМ НАЧИСЛЕНО {amount} USDT!**\n\n💰 НОВЫЙ БАЛАНС: {new_balance} USDT")
        
        elif action == "subtract":
            if amount > user["balance"]:
                await message.answer(f"❌ НЕДОСТАТОЧНО СРЕДСТВ! БАЛАНС ПОЛЬЗОВАТЕЛЯ: {user['balance']} USDT")
                return
            
            new_balance = user["balance"] - amount
            update_balance(user_id, new_balance)
            
            await message.answer(
                f"✅ **СПИСАНО {amount} USDT**\n\n"
                f"👤 ПОЛЬЗОВАТЕЛЬ: @{username}\n"
                f"📊 СТАРЫЙ БАЛАНС: {user['balance'] + amount} USDT\n"
                f"📊 НОВЫЙ БАЛАНС: {new_balance} USDT",
                parse_mode="Markdown",
                reply_markup=admin_keyboard()
            )
            
            await notify_admins(message.bot, f"➖ АДМИН СПИСАЛ {amount} USDT У @{username}")
            await notify_user(message.bot, user_id, f"➖ **СПИСАНО {amount} USDT**\n\n💰 НОВЫЙ БАЛАНС: {new_balance} USDT")
        
        await state.clear()
        
    except:
        await message.answer("❌ ВВЕДИТЕ ЧИСЛО")
