import sqlite3
from aiogram import Router, F, types
from aiogram.filters import Command
from config import ADMIN_IDS
from database import *

router = Router()

# Фильтр для админов
def admin_filter(message: types.Message):
    return message.from_user.id in ADMIN_IDS

@router.message(Command("add"), admin_filter)
async def add_balance(message: types.Message):
    try:
        args = message.text.split()
        username = args[1].replace('@', '')
        amount = float(args[2])
        user = get_user_by_username(username)
        if user:
            update_balance(user[0], amount)
            await message.reply(f"✅ Начислено {amount} USDT @{username}")
        else:
            await message.reply("❌ Пользователь не найден")
    except:
        await message.reply("❌ /add @username сумма")

@router.message(Command("remove"), admin_filter)
async def remove_balance(message: types.Message):
    try:
        args = message.text.split()
        username = args[1].replace('@', '')
        amount = float(args[2])
        user = get_user_by_username(username)
        if user:
            update_balance(user[0], -amount)
            await message.reply(f"✅ Списано {amount} USDT у @{username}")
        else:
            await message.reply("❌ Пользователь не найден")
    except:
        await message.reply("❌ /remove @username сумма")

@router.message(Command("reset"), admin_filter)
async def reset_balance(message: types.Message):
    try:
        args = message.text.split()
        username = args[1].replace('@', '')
        user = get_user_by_username(username)
        if user:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (user[0],))
            conn.commit()
            conn.close()
            await message.reply(f"✅ Баланс обнулён у @{username}")
        else:
            await message.reply("❌ Пользователь не найден")
    except:
        await message.reply("❌ /reset @username")

@router.message(Command("ban"), admin_filter)
async def ban(message: types.Message):
    try:
        args = message.text.split()
        username = args[1].replace('@', '')
        user = get_user_by_username(username)
        if user:
            ban_user(user[0])
            await message.reply(f"✅ @{username} забанен")
        else:
            await message.reply("❌ Пользователь не найден")
    except:
        await message.reply("❌ /ban @username")

@router.message(Command("unban"), admin_filter)
async def unban(message: types.Message):
    try:
        args = message.text.split()
        username = args[1].replace('@', '')
        user = get_user_by_username(username)
        if user:
            unban_user(user[0])
            await message.reply(f"✅ @{username} разбанен")
        else:
            await message.reply("❌ Пользователь не найден")
    except:
        await message.reply("❌ /unban @username")

@router.message(Command("broadcast"), admin_filter)
async def broadcast(message: types.Message):
    msg_text = message.text.replace('/broadcast', '').strip()
    if not msg_text:
        await message.reply("❌ /broadcast текст")
        return
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    success = 0
    for user in users:
        try:
            await message.bot.send_message(user[0], f"📢 Рассылка:\n\n{msg_text}")
            success += 1
        except:
            pass
    await message.reply(f"✅ Отправлено {success} пользователям")

@router.message(Command("find"), admin_filter)
async def find_user(message: types.Message):
    try:
        args = message.text.split()
        username = args[1].replace('@', '')
        user = get_user_by_username(username)
        if user:
            user_id, balance = user[0], user[2]
            withdrawals = get_last_withdrawals(user_id, 5)
            text = f"👤 @{username}\n💰 {balance} USDT\n\n📋 Последние 5 заявок:\n"
            for w in withdrawals:
                status_emoji = "⏳" if w[1] == "pending" else ("✅" if w[1] == "approved" else "❌")
                text += f"{status_emoji} {w[0]} USDT - {w[1]} ({w[2][:16]})\n"
            await message.reply(text)
        else:
            await message.reply("❌ Пользователь не найден")
    except:
        await message.reply("❌ /find @username")

@router.message(Command("withdrawals"), admin_filter)
async def withdrawals_list(message: types.Message):
    withdrawals = get_all_withdrawals('pending')
    if not withdrawals:
        await message.reply("📭 Нет заявок")
        return
    for w in withdrawals[:10]:
        text = f"🆔 #{w[0]}\n👤 {w[1]}\n💰 {w[2]} USDT\n💳 {w[3]}\n📝 {w[4]}\n\n/approve_{w[0]} - Одобрить\n/reject_{w[0]} - Отклонить"
        await message.reply(text)

@router.message(Command("appeals"), admin_filter)
async def appeals_list(message: types.Message):
    appeals = get_all_appeals()
    if not appeals:
        await message.reply("📭 Нет обращений")
        return
    for a in appeals[:10]:
        text = f"🆔 #{a[0]}\n👤 {a[1]}\n💬 {a[2]}\n\n/reply_{a[0]} текст"
        await message.reply(text)

@router.message(admin_filter)
async def handle_admin_actions(message: types.Message):
    text = message.text
    if text.startswith('/approve_'):
        try:
            w_id = int(text.split('_')[1])
            update_withdrawal_status(w_id, 'approved')
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT user_id FROM withdrawals WHERE id = ?", (w_id,))
            user_id = c.fetchone()[0]
            conn.close()
            await message.bot.send_message(user_id, "✅ Ваша заявка была одобрена, ожидайте")
            await message.reply(f"✅ Заявка #{w_id} одобрена")
        except:
            await message.reply("❌ Ошибка")
    elif text.startswith('/reject_'):
        try:
            w_id = int(text.split('_')[1])
            update_withdrawal_status(w_id, 'rejected')
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT user_id FROM withdrawals WHERE id = ?", (w_id,))
            user_id = c.fetchone()[0]
            conn.close()
            await message.bot.send_message(user_id, "❌ Ваша заявка отклонена, обратитесь в поддержку")
            await message.reply(f"✅ Заявка #{w_id} отклонена")
        except:
            await message.reply("❌ Ошибка")
    elif text.startswith('/reply_'):
        try:
            parts = text.split(' ', 1)
            a_id = int(parts[0].split('_')[1])
            reply_msg = parts[1]
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT user_id FROM appeals WHERE id = ?", (a_id,))
            user_id = c.fetchone()[0]
            conn.close()
            update_appeal_status(a_id, 'answered')
            await message.bot.send_message(user_id, f"🆘 Ответ администратора:\n\n{reply_msg}")
            await message.reply(f"✅ Ответ отправлен")
        except:
            await message.reply("❌ /reply_123 текст")
