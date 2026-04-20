import sqlite3
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
from database import *

router = Router()

# Проверка админа
def is_admin(user_id):
    return user_id in ADMIN_IDS

# Главное админ-меню
async def admin_main_menu(message: types.Message, text: str = "👑 *Админ-панель*\n\nВыберите действие:"):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Управление балансом", callback_data="admin_balance")],
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users")],
        [InlineKeyboardButton(text="📋 Заявки на вывод", callback_data="admin_withdrawals")],
        [InlineKeyboardButton(text="🆘 Обращения в поддержку", callback_data="admin_appeals")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")]
    ])
    if isinstance(message, types.Message):
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# === ВХОД В АДМИНКУ ===
@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if is_admin(message.from_user.id):
        await admin_main_menu(message)
    else:
        await message.answer("❌ У вас нет доступа к админ-панели")

# === УПРАВЛЕНИЕ БАЛАНСОМ ===
@router.callback_query(F.data == "admin_balance")
async def admin_balance_menu(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Начислить", callback_data="admin_add")],
        [InlineKeyboardButton(text="➖ Списать", callback_data="admin_remove")],
        [InlineKeyboardButton(text="🔄 Обнулить", callback_data="admin_reset")],
        [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_find")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text("💰 *Управление балансом*\n\nВыберите действие:", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "admin_add")
async def admin_add_balance(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_add")
    await callback.message.edit_text("Введите: `@username сумма`\n\nПример: `@ivan 100`", parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_remove")
async def admin_remove_balance(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_remove")
    await callback.message.edit_text("Введите: `@username сумма`\n\nПример: `@ivan 50`", parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_reset")
async def admin_reset_balance(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_reset")
    await callback.message.edit_text("Введите: `@username`\n\nПример: `@ivan`", parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_find")
async def admin_find_user(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_find")
    await callback.message.edit_text("Введите: `@username`\n\nПример: `@ivan`", parse_mode="Markdown")
    await callback.answer()

# === УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ===
@router.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔨 Бан", callback_data="admin_ban")],
        [InlineKeyboardButton(text="🔓 Разбан", callback_data="admin_unban")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text("👥 *Управление пользователями*\n\nВыберите действие:", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "admin_ban")
async def admin_ban_user(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_ban")
    await callback.message.edit_text("Введите: `@username`\n\nПример: `@ivan`", parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_unban")
async def admin_unban_user(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_unban")
    await callback.message.edit_text("Введите: `@username`\n\nПример: `@ivan`", parse_mode="Markdown")
    await callback.answer()

# === ЗАЯВКИ НА ВЫВОД ===
@router.callback_query(F.data == "admin_withdrawals")
async def admin_withdrawals_list(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    withdrawals = get_all_withdrawals('pending')
    if not withdrawals:
        await callback.message.edit_text("📭 Нет активных заявок на вывод", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]]))
        await callback.answer()
        return
    
    for w in withdrawals[:10]:
        text = f"🆔 *Заявка #{w[0]}*\n👤 User ID: `{w[1]}`\n💰 Сумма: {w[2]} USDT\n💳 Способ: {w[3]}\n📝 Реквизиты: {w[4]}\n📅 Создана: {w[6][:16]}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_approve_{w[0]}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{w[0]}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ])
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_withdraw(callback: types.CallbackQuery):
    w_id = int(callback.data.split("_")[2])
    update_withdrawal_status(w_id, 'approved')
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM withdrawals WHERE id = ?", (w_id,))
    user_id = c.fetchone()[0]
    conn.close()
    await callback.bot.send_message(user_id, "✅ Ваша заявка была одобрена, ожидайте")
    await callback.message.edit_text(f"✅ Заявка #{w_id} одобрена")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_withdraw(callback: types.CallbackQuery):
    w_id = int(callback.data.split("_")[2])
    update_withdrawal_status(w_id, 'rejected')
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM withdrawals WHERE id = ?", (w_id,))
    user_id = c.fetchone()[0]
    conn.close()
    await callback.bot.send_message(user_id, "❌ Ваша заявка отклонена, обратитесь в поддержку")
    await callback.message.edit_text(f"✅ Заявка #{w_id} отклонена")
    await callback.answer()

# === ОБРАЩЕНИЯ В ПОДДЕРЖКУ ===
@router.callback_query(F.data == "admin_appeals")
async def admin_appeals_list(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    appeals = get_all_appeals()
    if not appeals:
        await callback.message.edit_text("📭 Нет обращений в поддержку", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]]))
        await callback.answer()
        return
    
    for a in appeals[:10]:
        text = f"🆔 *Обращение #{a[0]}*\n👤 User ID: `{a[1]}`\n💬 Сообщение: {a[2]}\n📅 Создана: {a[4][:16]}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Ответить", callback_data=f"admin_reply_{a[0]}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ])
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_reply_"))
async def admin_reply_appeal(callback: types.CallbackQuery, state: FSMContext):
    a_id = int(callback.data.split("_")[2])
    await state.update_data(reply_appeal_id=a_id)
    await state.set_state("admin_waiting_reply")
    await callback.message.edit_text("Введите текст ответа для пользователя:")
    await callback.answer()

# === РАССЫЛКА ===
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_broadcast")
    await callback.message.edit_text("Введите текст рассылки:")
    await callback.answer()

# === СТАТИСТИКА ===
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE consent = 1")
    active_users = c.fetchone()[0]
    c.execute("SELECT SUM(amount) FROM withdrawals WHERE status = 'approved'")
    total_paid = c.fetchone()[0] or 0
    c.execute("SELECT AVG(balance) FROM users")
    avg_balance = c.fetchone()[0] or 0
    conn.close()
    
    text = f"📊 *Статистика*\n\n👥 Всего пользователей: {total_users}\n✅ Активных (согласие): {active_users}\n💰 Всего выплачено: {total_paid} USDT\n📈 Средний баланс: {avg_balance:.2f} USDT"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

# === НАВИГАЦИЯ ===
@router.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery):
    await admin_main_menu(callback)

@router.callback_query(F.data == "admin_close")
async def admin_close(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()

# === ОБРАБОТЧИКИ ВВОДА ===
@router.message(lambda msg: msg.from_user.id in ADMIN_IDS)
async def handle_admin_input(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state == "admin_waiting_add":
        try:
            parts = message.text.split()
            username = parts[0].replace('@', '')
            amount = float(parts[1])
            user = get_user_by_username(username)
            if user:
                update_balance(user[0], amount)
                await message.answer(f"✅ Начислено {amount} USDT @{username}")
            else:
                await message.answer("❌ Пользователь не найден")
        except:
            await message.answer("❌ Ошибка! Используйте: @username сумма")
        await state.clear()
        await admin_main_menu(message)
    
    elif current_state == "admin_waiting_remove":
        try:
            parts = message.text.split()
            username = parts[0].replace('@', '')
            amount = float(parts[1])
            user = get_user_by_username(username)
            if user:
                update_balance(user[0], -amount)
                await message.answer(f"✅ Списано {amount} USDT у @{username}")
            else:
                await message.answer("❌ Пользователь не найден")
        except:
            await message.answer("❌ Ошибка! Используйте: @username сумма")
        await state.clear()
        await admin_main_menu(message)
    
    elif current_state == "admin_waiting_reset":
        try:
            username = message.text.replace('@', '').strip()
            user = get_user_by_username(username)
            if user:
                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                c.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (user[0],))
                conn.commit()
                conn.close()
                await message.answer(f"✅ Баланс обнулён у @{username}")
            else:
                await message.answer("❌ Пользователь не найден")
        except:
            await message.answer("❌ Ошибка! Используйте: @username")
        await state.clear()
        await admin_main_menu(message)
    
    elif current_state == "admin_waiting_find":
        try:
            username = message.text.replace('@', '').strip()
            user = get_user_by_username(username)
            if user:
                user_id, balance = user[0], user[2]
                withdrawals = get_last_withdrawals(user_id, 5)
                text = f"👤 @{username}\n💰 {balance} USDT\n\n📋 Последние 5 заявок:\n"
                for w in withdrawals:
                    status_emoji = "⏳" if w[1] == "pending" else ("✅" if w[1] == "approved" else "❌")
                    text += f"{status_emoji} {w[0]} USDT - {w[1]} ({w[2][:16]})\n"
                await message.answer(text)
            else:
                await message.answer("❌ Пользователь не найден")
        except:
            await message.answer("❌ Ошибка! Используйте: @username")
        await state.clear()
        await admin_main_menu(message)
    
    elif current_state == "admin_waiting_ban":
        try:
            username = message.text.replace('@', '').strip()
            user = get_user_by_username(username)
            if user:
                ban_user(user[0])
                await message.answer(f"✅ @{username} забанен")
            else:
                await message.answer("❌ Пользователь не найден")
        except:
            await message.answer("❌ Ошибка! Используйте: @username")
        await state.clear()
        await admin_main_menu(message)
    
    elif current_state == "admin_waiting_unban":
        try:
            username = message.text.replace('@', '').strip()
            user = get_user_by_username(username)
            if user:
                unban_user(user[0])
                await message.answer(f"✅ @{username} разбанен")
            else:
                await message.answer("❌ Пользователь не найден")
        except:
            await message.answer("❌ Ошибка! Используйте: @username")
        await state.clear()
        await admin_main_menu(message)
    
    elif current_state == "admin_waiting_reply":
        reply_text = message.text
        data = await state.get_data()
        a_id = data.get('reply_appeal_id')
        if a_id:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT user_id FROM appeals WHERE id = ?", (a_id,))
            user_id = c.fetchone()[0]
            conn.close()
            update_appeal_status(a_id, 'answered')
            await message.bot.send_message(user_id, f"🆘 *Ответ администратора:*\n\n{reply_text}")
            await message.answer(f"✅ Ответ отправлен на обращение #{a_id}")
        await state.clear()
        await admin_main_menu(message)
    
    elif current_state == "admin_waiting_broadcast":
        broadcast_text = message.text
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE consent = 1")
        users = c.fetchall()
        conn.close()
        success = 0
        for user in users:
            try:
                await message.bot.send_message(user[0], f"📢 *Рассылка*\n\n{broadcast_text}", parse_mode="Markdown")
                success += 1
            except:
                pass
        await message.answer(f"✅ Рассылка отправлена {success} пользователям")
        await state.clear()
        await admin_main_menu(message)
