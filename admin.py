from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_user_by_username, update_user, load_users, is_banned, ban_user, unban_user,
    load_withdraws, update_withdraw_status, load_reviews, get_user_by_id,
    delete_old_withdraws
)
from keyboards import admin_keyboard, back_keyboard, cancel_keyboard, main_keyboard, withdraw_action_keyboard
from utils import notify_admins, notify_all_users
from config import ADMIN_IDS

admin_router = Router()

class AdminState(StatesGroup):
    wait_username = State()
    wait_amount = State()
    wait_new_balance = State()
    wait_rating = State()
    wait_broadcast = State()
    wait_broadcast_confirm = State()

def is_admin(user_id):
    return user_id in ADMIN_IDS

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("👑 **АДМИН-ПАНЕЛЬ**", reply_markup=admin_keyboard(), parse_mode="Markdown")
    else:
        await message.answer("❌ НЕТ ДОСТУПА")

@admin_router.message(lambda msg: msg.text == "🔙 ВЫЙТИ" and is_admin(msg.from_user.id))
async def exit_admin(message: types.Message):
    await message.answer("🔙 ВЫХОД", reply_markup=main_keyboard())

# ========== ЗАЧИСЛИТЬ ==========
@admin_router.message(lambda msg: msg.text == "➕ ЗАЧИСЛИТЬ БАЛАНС" and is_admin(msg.from_user.id))
async def add_start(message: types.Message, state: FSMContext):
    await message.answer("ВВЕДИТЕ USERNAME (БЕЗ @):", reply_markup=back_keyboard())
    await state.set_state(AdminState.wait_username)

@admin_router.message(AdminState.wait_username)
async def add_get_user(message: types.Message, state: FSMContext):
    if message.text == "🔙 НАЗАД":
        await state.clear()
        await message.answer("АДМИН-ПАНЕЛЬ", reply_markup=admin_keyboard())
        return
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        return
    await state.update_data(username=message.text)
    await message.answer(f"👤 @{user['username']}\n💰 БАЛАНС: {user['balance']} USDT\n\nВВЕДИТЕ СУММУ:", reply_markup=cancel_keyboard())
    await state.set_state(AdminState.wait_amount)

@admin_router.message(AdminState.wait_amount)
async def add_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ ОТМЕНА":
        await state.clear()
        await message.answer("ОТМЕНЕНО", reply_markup=admin_keyboard())
        return
    try:
        amount = float(message.text)
        data = await state.get_data()
        user = get_user_by_username(data["username"])
        new_balance = user["balance"] + amount
        update_user(user["id"], {"balance": new_balance})
        await message.answer(f"✅ ЗАЧИСЛЕНО {amount} USDT\n💰 НОВЫЙ БАЛАНС: {new_balance} USDT", reply_markup=admin_keyboard())
        await notify_admins(message.bot, f"💰 АДМИН ЗАЧИСЛИЛ {amount} USDT @{user['username']}")
        try:
            await message.bot.send_message(user["id"], f"💰 ЗАЧИСЛЕНО {amount} USDT!\nБАЛАНС: {new_balance} USDT")
        except:
            pass
        await state.clear()
    except:
        await message.answer("❌ ВВЕДИТЕ ЧИСЛО")

# ========== СПИСАТЬ ==========
@admin_router.message(lambda msg: msg.text == "➖ СПИСАТЬ БАЛАНС" and is_admin(msg.from_user.id))
async def sub_start(message: types.Message, state: FSMContext):
    await message.answer("ВВЕДИТЕ USERNAME (БЕЗ @):", reply_markup=back_keyboard())
    await state.set_state(AdminState.wait_username)

@admin_router.message(AdminState.wait_username)
async def sub_get_user(message: types.Message, state: FSMContext):
    if message.text == "🔙 НАЗАД":
        await state.clear()
        await message.answer("АДМИН-ПАНЕЛЬ", reply_markup=admin_keyboard())
        return
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        return
    await state.update_data(username=message.text)
    await message.answer(f"👤 @{user['username']}\n💰 БАЛАНС: {user['balance']} USDT\n\nВВЕДИТЕ СУММУ СПИСАНИЯ:", reply_markup=cancel_keyboard())
    await state.set_state(AdminState.wait_amount)

@admin_router.message(AdminState.wait_amount)
async def sub_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ ОТМЕНА":
        await state.clear()
        await message.answer("ОТМЕНЕНО", reply_markup=admin_keyboard())
        return
    try:
        amount = float(message.text)
        data = await state.get_data()
        user = get_user_by_username(data["username"])
        if amount > user["balance"]:
            await message.answer("❌ НЕДОСТАТОЧНО СРЕДСТВ")
            return
        new_balance = user["balance"] - amount
        update_user(user["id"], {"balance": new_balance})
        await message.answer(f"✅ СПИСАНО {amount} USDT\n💰 НОВЫЙ БАЛАНС: {new_balance} USDT", reply_markup=admin_keyboard())
        await notify_admins(message.bot, f"➖ АДМИН СПИСАЛ {amount} USDT У @{user['username']}")
        try:
            await message.bot.send_message(user["id"], f"➖ СПИСАНО {amount} USDT!\nБАЛАНС: {new_balance} USDT")
        except:
            pass
        await state.clear()
    except:
        await message.answer("❌ ВВЕДИТЕ ЧИСЛО")

# ========== ИЗМЕНИТЬ ==========
@admin_router.message(lambda msg: msg.text == "🔧 ИЗМЕНИТЬ БАЛАНС" and is_admin(msg.from_user.id))
async def set_start(message: types.Message, state: FSMContext):
    await message.answer("ВВЕДИТЕ USERNAME (БЕЗ @):", reply_markup=back_keyboard())
    await state.set_state(AdminState.wait_username)

@admin_router.message(AdminState.wait_username)
async def set_get_user(message: types.Message, state: FSMContext):
    if message.text == "🔙 НАЗАД":
        await state.clear()
        await message.answer("АДМИН-ПАНЕЛЬ", reply_markup=admin_keyboard())
        return
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        return
    await state.update_data(username=message.text)
    await message.answer(f"👤 @{user['username']}\n💰 БАЛАНС: {user['balance']} USDT\n\nВВЕДИТЕ НОВЫЙ БАЛАНС:", reply_markup=cancel_keyboard())
    await state.set_state(AdminState.wait_new_balance)

@admin_router.message(AdminState.wait_new_balance)
async def set_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ ОТМЕНА":
        await state.clear()
        await message.answer("ОТМЕНЕНО", reply_markup=admin_keyboard())
        return
    try:
        new_balance = float(message.text)
        data = await state.get_data()
        user = get_user_by_username(data["username"])
        old_balance = user["balance"]
        update_user(user["id"], {"balance": new_balance})
        await message.answer(f"✅ БАЛАНС ИЗМЕНЁН\n📊 {old_balance} USDT → {new_balance} USDT", reply_markup=admin_keyboard())
        await notify_admins(message.bot, f"🔧 АДМИН ИЗМЕНИЛ БАЛАНС @{user['username']}\n{old_balance} → {new_balance} USDT")
        try:
            await message.bot.send_message(user["id"], f"🔧 ВАШ БАЛАНС ИЗМЕНЁН!\n{old_balance} → {new_balance} USDT")
        except:
            pass
        await state.clear()
    except:
        await message.answer("❌ ВВЕДИТЕ ЧИСЛО")

# ========== ЗАЯВКИ НА ВЫВОД ==========
@admin_router.message(lambda msg: msg.text == "✅ ЗАЯВКИ НА ВЫВОД" and is_admin(msg.from_user.id))
async def list_withdraws(message: types.Message):
    delete_old_withdraws(1)
    withdraws = load_withdraws()
    pending = [w for w in withdraws if w["status"] == "pending"]
    if not pending:
        await message.answer("📭 НЕТ АКТИВНЫХ ЗАЯВОК", reply_markup=admin_keyboard())
        return
    for w in pending:
        text = f"💰 **ЗАЯВКА**\n\n👤 @{w['username'] or 'нет'} (ID: {w['user_id']})\n💵 {w['amount']} USDT\n💳 {w['method']}\n📝 {w['details']}\n📅 {w['created_at'][:19]}"
        await message.answer(text, parse_mode="Markdown", reply_markup=withdraw_action_keyboard(w["id"]))

@admin_router.callback_query(lambda c: c.data.startswith("approve_"))
async def approve_withdraw(callback: types.CallbackQuery):
    wid = int(callback.data.split("_")[1])
    w = update_withdraw_status(wid, "approved")
    if w:
        user = get_user_by_id(w["user_id"])
        if user:
            new_balance = user["balance"] - w["amount"]
            new_total = user.get("total_withdrawn", 0) + w["amount"]
            update_user(w["user_id"], {"balance": new_balance, "total_withdrawn": new_total})
            try:
                await callback.bot.send_message(w["user_id"], f"✅ ЗАЯВКА ОДОБРЕНА!\nСУММА: {w['amount']} USDT\nНОВЫЙ БАЛАНС: {new_balance} USDT")
            except:
                pass
            await notify_admins(callback.bot, f"✅ ЗАЯВКА ОДОБРЕНА\nПОЛЬЗОВАТЕЛЬ: @{user['username']}\nСУММА: {w['amount']} USDT")
        await callback.message.edit_text(f"✅ ОДОБРЕНО\n{callback.message.text}")
    await callback.answer()

@admin_router.callback_query(lambda c: c.data.startswith("reject_"))
async def reject_withdraw(callback: types.CallbackQuery):
    wid = int(callback.data.split("_")[1])
    w = update_withdraw_status(wid, "rejected")
    if w:
        try:
            await callback.bot.send_message(w["user_id"], f"❌ ЗАЯВКА ОТКЛОНЕНА!\nСУММА: {w['amount']} USDT\nОБРАТИТЕСЬ В ПОДДЕРЖКУ")
        except:
            pass
        await notify_admins(callback.bot, f"❌ ЗАЯВКА ОТКЛОНЕНА\nПОЛЬЗОВАТЕЛЬ: @{w['username']}\nСУММА: {w['amount']} USDT")
        await callback.message.edit_text(f"❌ ОТКЛОНЕНО\n{callback.message.text}")
    await callback.answer()

# ========== УПРАВЛЕНИЕ РЕЙТИНГОМ ==========
@admin_router.message(lambda msg: msg.text == "⭐ УПРАВЛЕНИЕ РЕЙТИНГОМ" and is_admin(msg.from_user.id))
async def rating_start(message: types.Message, state: FSMContext):
    await message.answer("ВВЕДИТЕ USERNAME (БЕЗ @):", reply_markup=back_keyboard())
    await state.set_state(AdminState.wait_username)

@admin_router.message(AdminState.wait_username)
async def rating_get_user(message: types.Message, state: FSMContext):
    if message.text == "🔙 НАЗАД":
        await state.clear()
        await message.answer("АДМИН-ПАНЕЛЬ", reply_markup=admin_keyboard())
        return
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        return
    await state.update_data(username=message.text)
    await message.answer(f"👤 @{user['username']}\n🏆 ТЕКУЩИЙ РЕЙТИНГ: {user.get('rating', 0)}\n\nВВЕДИТЕ НОВОЕ МЕСТО (0 = НЕ В РЕЙТИНГЕ):", reply_markup=cancel_keyboard())
    await state.set_state(AdminState.wait_rating)

@admin_router.message(AdminState.wait_rating)
async def rating_set(message: types.Message, state: FSMContext):
    if message.text == "❌ ОТМЕНА":
        await state.clear()
        await message.answer("ОТМЕНЕНО", reply_markup=admin_keyboard())
        return
    try:
        rating = int(message.text)
        data = await state.get_data()
        user = get_user_by_username(data["username"])
        update_user(user["id"], {"rating": rating})
        rating_text = "НЕ В РЕЙТИНГЕ" if rating == 0 else str(rating)
        await message.answer(f"✅ РЕЙТИНГ ОБНОВЛЁН\n🏆 @{user['username']} → {rating_text}", reply_markup=admin_keyboard())
        await notify_admins(message.bot, f"⭐ АДМИН ОБНОВИЛ РЕЙТИНГ @{user['username']} → {rating_text}")
        await state.clear()
    except:
        await message.answer("❌ ВВЕДИТЕ ЧИСЛО")

# ========== СПИСОК ОТЗЫВОВ ==========
@admin_router.message(lambda msg: msg.text == "📋 СПИСОК ОТЗЫВОВ" and is_admin(msg.from_user.id))
async def list_reviews(message: types.Message):
    reviews = load_reviews()
    if not reviews:
        await message.answer("📭 НЕТ ОТЗЫВОВ", reply_markup=admin_keyboard())
        return
    for r in reviews[-20:]:
        stars = "⭐" * r["rating"]
        name = "АНОНИМ" if r.get("is_anonymous") else f"@{r.get('username') or 'НЕТ'}"
        text = f"⭐ **ОТЗЫВ**\n\n👤 {name}\n⭐ {r['rating']}/5 {stars}\n💬 {r.get('comment', 'БЕЗ КОММЕНТАРИЯ')}\n📅 {r['created_at'][:19]}"
        await message.answer(text, parse_mode="Markdown")
    await message.answer("📊 ПОКАЗАНЫ ПОСЛЕДНИЕ 20 ОТЗЫВОВ", reply_markup=admin_keyboard())

# ========== РАССЫЛКА ==========
@admin_router.message(lambda msg: msg.text == "📢 РАССЫЛКА" and is_admin(msg.from_user.id))
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer("📢 ВВЕДИТЕ ТЕКСТ РАССЫЛКИ:", reply_markup=back_keyboard())
    await state.set_state(AdminState.wait_broadcast)

@admin_router.message(AdminState.wait_broadcast)
async def broadcast_text(message: types.Message, state: FSMContext):
    if message.text == "🔙 НАЗАД":
        await state.clear()
        await message.answer("АДМИН-ПАНЕЛЬ", reply_markup=admin_keyboard())
        return
    await state.update_data(text=message.text)
    await message.answer(f"📢 ТЕКСТ:\n\n{message.text}\n\nОТПРАВИТЬ?", reply_markup=types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="✅ ДА"), types.KeyboardButton(text="❌ НЕТ")]], resize_keyboard=True))
    await state.set_state(AdminState.wait_broadcast_confirm)

@admin_router.message(AdminState.wait_broadcast_confirm)
async def broadcast_confirm(message: types.Message, state: FSMContext):
    if message.text == "❌ НЕТ":
        await state.clear()
        await message.answer("ОТМЕНЕНО", reply_markup=admin_keyboard())
        return
    if message.text == "✅ ДА":
        data = await state.get_data()
        await message.answer("📢 НАЧИНАЮ РАССЫЛКУ...")
        await notify_all_users(message.bot, f"📢 **РАССЫЛКА ОТ АДМИНИСТРАЦИИ**\n\n{data.get('text')}")
        await message.answer("✅ РАССЫЛКА ЗАВЕРШЕНА!", reply_markup=admin_keyboard())
        await state.clear()

# ========== БАН/РАЗБАН ==========
@admin_router.message(lambda msg: msg.text == "👥 БАН/РАЗБАН" and is_admin(msg.from_user.id))
async def ban_menu(message: types.Message):
    kb = [
        [types.KeyboardButton(text="🔨 ЗАБАНИТЬ")],
        [types.KeyboardButton(text="🔓 РАЗБАНИТЬ")],
        [types.KeyboardButton(text="🔙 НАЗАД")]
    ]
    await message.answer("👥 УПРАВЛЕНИЕ БАНАМИ", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@admin_router.message(lambda msg: msg.text == "🔨 ЗАБАНИТЬ" and is_admin(msg.from_user.id))
async def ban_user_start(message: types.Message, state: FSMContext):
    await message.answer("ВВЕДИТЕ USERNAME (БЕЗ @):", reply_markup=back_keyboard())
    await state.set_state(AdminState.wait_username)

@admin_router.message(AdminState.wait_username)
async def ban_user_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 НАЗАД":
        await state.clear()
        await message.answer("АДМИН-ПАНЕЛЬ", reply_markup=admin_keyboard())
        return
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        return
    if ban_user(user["id"]):
        await message.answer(f"✅ @{user['username']} ЗАБАНЕН", reply_markup=admin_keyboard())
        await notify_admins(message.bot, f"🔨 АДМИН ЗАБАНИЛ @{user['username']}")
        try:
            await message.bot.send_message(user["id"], "❌ ВЫ ЗАБАНЕНЫ")
        except:
            pass
    else:
        await message.answer("⚠️ УЖЕ В БАНЕ")
    await state.clear()

@admin_router.message(lambda msg: msg.text == "🔓 РАЗБАНИТЬ" and is_admin(msg.from_user.id))
async def unban_user_start(message: types.Message, state: FSMContext):
    await message.answer("ВВЕДИТЕ USERNAME (БЕЗ @):", reply_markup=back_keyboard())
    await state.set_state(AdminState.wait_username)

@admin_router.message(AdminState.wait_username)
async def unban_user_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 НАЗАД":
        await state.clear()
        await message.answer("АДМИН-ПАНЕЛЬ", reply_markup=admin_keyboard())
        return
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        return
    if unban_user(user["id"]):
        await message.answer(f"✅ @{user['username']} РАЗБАНЕН", reply_markup=admin_keyboard())
        await notify_admins(message.bot, f"🔓 АДМИН РАЗБАНИЛ @{user['username']}")
        try:
            await message.bot.send_message(user["id"], "✅ ВЫ РАЗБАНЕНЫ")
        except:
            pass
    else:
        await message.answer("⚠️ НЕ В БАНЕ")
    await state.clear()

# ========== ПРОСМОТР ПОЛЬЗОВАТЕЛЯ ==========
@admin_router.message(lambda msg: msg.text == "📊 ПРОСМОТР ПОЛЬЗОВАТЕЛЯ" and is_admin(msg.from_user.id))
async def view_user_start(message: types.Message, state: FSMContext):
    await message.answer("ВВЕДИТЕ USERNAME (БЕЗ @):", reply_markup=back_keyboard())
    await state.set_state(AdminState.wait_username)

@admin_router.message(AdminState.wait_username)
async def view_user_result(message: types.Message, state: FSMContext):
    if message.text == "🔙 НАЗАД":
        await state.clear()
        await message.answer("АДМИН-ПАНЕЛЬ", reply_markup=admin_keyboard())
        return
    user = get_user_by_username(message.text)
    if not user:
        await message.answer("❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
        await state.clear()
        return
    withdraws = load_withdraws()
    user_withdraws = [w for w in withdraws if w["user_id"] == user["id"]]
    text = f"📊 **ПОЛЬЗОВАТЕЛЬ**\n\n👤 @{user['username'] or 'нет'}\n🆔 ID: {user['id']}\n💰 БАЛАНС: {user['balance']} USDT\n📤 ВЫВЕДЕНО: {user['total_withdrawn']} USDT\n🏆 РЕЙТИНГ: {user.get('rating', 0)}\n⭐ ОТЗЫВОВ: {user.get('rating_count', 0)}\n📜 ЗАЯВОК: {len(user_withdraws)}\n📅 ДАТА: {user['joined'][:19]}"
    await message.answer(text, parse_mode="Markdown", reply_markup=admin_keyboard())
    await state.clear()
