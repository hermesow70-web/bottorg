from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    load_users, get_user_by_id, get_user_by_username, update_user_by_id, update_user_by_username,
    load_banned, save_banned, load_withdraws, save_withdraws, load_reviews, save_reviews,
    get_rating_list
)
from keyboards import admin_keyboard, back_keyboard, cancel_keyboard, main_keyboard
from utils import notify_admins, notify_all_users
from config import ADMIN_IDS

admin_router = Router()

class AdminStates(StatesGroup):
    add_balance_username = State()
    add_balance_amount = State()
    subtract_balance_username = State()
    subtract_balance_amount = State()
    set_balance_username = State()
    set_balance_amount = State()
    set_rating_username = State()
    set_rating_value = State()
    broadcast_text = State()
    broadcast_confirm = State()
    ban_username = State()
    unban_username = State()
    view_user_username = State()

def is_admin(user_id):
    return user_id in ADMIN_IDS

def withdraw_action_keyboard(wid):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_withdraw_{wid}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_withdraw_{wid}")]
    ])

@admin_router.message(Command("admin"))
async def admin_login(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("👑 **АДМИН-ПАНЕЛЬ**", reply_markup=admin_keyboard(), parse_mode="Markdown")
    else:
        await message.answer("❌ **Нет доступа**", parse_mode="Markdown")

@admin_router.message(lambda msg: msg.text == "🔙 ВЫЙТИ ИЗ АДМИНКИ" and is_admin(msg.from_user.id))
async def exit_admin(message: types.Message):
    await message.answer("🔙 **Вы вышли из админ-панели**", reply_markup=main_keyboard(), parse_mode="Markdown")

# ========== ЗАЧИСЛИТЬ БАЛАНС ==========
@admin_router.message(lambda msg: msg.text == "➕ ЗАЧИСЛИТЬ БАЛАНС" and is_admin(msg.from_user.id))
async def add_balance_start(message: types.Message, state: FSMContext):
    await message.answer(
        "➕ **ЗАЧИСЛЕНИЕ БАЛАНСА**\n\n"
        "Введите **username** пользователя (без @):",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(AdminStates.add_balance_username)

@admin_router.message(AdminStates.add_balance_username)
async def add_balance_user(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    username = message.text.strip().replace("@", "")
    user = get_user_by_username(username)
    
    if not user:
        await message.answer(f"❌ **Пользователь @{username} не найден**\n\nПроверьте username и попробуйте снова:", parse_mode="Markdown")
        return
    
    await state.update_data(username=username)
    await message.answer(
        f"👤 **Пользователь:** @{user['username']}\n"
        f"💰 **Текущий баланс:** {user['balance']} USDT\n\n"
        f"💵 **Введите сумму для зачисления (USDT):**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.add_balance_amount)

@admin_router.message(AdminStates.add_balance_amount)
async def add_balance_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ **Операция отменена**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    try:
        amount = float(message.text)
        data = await state.get_data()
        username = data.get("username")
        user = get_user_by_username(username)
        
        if not user:
            await message.answer("❌ **Ошибка: пользователь не найден**", reply_markup=admin_keyboard())
            await state.clear()
            return
        
        new_balance = user['balance'] + amount
        update_user_by_username(username, {"balance": new_balance})
        
        await message.answer(
            f"✅ **Зачислено {amount} USDT** пользователю @{user['username']}\n"
            f"💰 **Новый баланс:** {new_balance} USDT",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        
        await notify_admins(
            message.bot,
            f"💰 **Админ зачислил {amount} USDT** пользователю @{user['username']}\n"
            f"📊 **Новый баланс:** {new_balance} USDT"
        )
        
        try:
            await message.bot.send_message(
                user["id"],
                f"💰 **Вам зачислено {amount} USDT!**\n\n"
                f"📊 **Ваш баланс:** {new_balance} USDT",
                parse_mode="Markdown"
            )
        except:
            pass
        
        await state.clear()
    except:
        await message.answer("❌ **Введите число (цифрами)**", parse_mode="Markdown")

# ========== СПИСАТЬ БАЛАНС ==========
@admin_router.message(lambda msg: msg.text == "➖ СПИСАТЬ БАЛАНС" and is_admin(msg.from_user.id))
async def subtract_balance_start(message: types.Message, state: FSMContext):
    await message.answer(
        "➖ **СПИСАНИЕ БАЛАНСА**\n\n"
        "Введите **username** пользователя (без @):",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(AdminStates.subtract_balance_username)

@admin_router.message(AdminStates.subtract_balance_username)
async def subtract_balance_user(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    username = message.text.strip().replace("@", "")
    user = get_user_by_username(username)
    
    if not user:
        await message.answer(f"❌ **Пользователь @{username} не найден**\n\nПроверьте username и попробуйте снова:", parse_mode="Markdown")
        return
    
    await state.update_data(username=username)
    await message.answer(
        f"👤 **Пользователь:** @{user['username']}\n"
        f"💰 **Текущий баланс:** {user['balance']} USDT\n\n"
        f"💵 **Введите сумму для списания (USDT):**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.subtract_balance_amount)

@admin_router.message(AdminStates.subtract_balance_amount)
async def subtract_balance_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ **Операция отменена**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    try:
        amount = float(message.text)
        data = await state.get_data()
        username = data.get("username")
        user = get_user_by_username(username)
        
        if not user:
            await message.answer("❌ **Ошибка: пользователь не найден**", reply_markup=admin_keyboard())
            await state.clear()
            return
        
        if amount > user['balance']:
            await message.answer(
                f"❌ **Недостаточно средств!**\n"
                f"💰 **Баланс пользователя:** {user['balance']} USDT\n"
                f"💵 **Запрошено списание:** {amount} USDT\n\n"
                f"Введите другую сумму:",
                parse_mode="Markdown"
            )
            return
        
        new_balance = user['balance'] - amount
        update_user_by_username(username, {"balance": new_balance})
        
        await message.answer(
            f"✅ **Списано {amount} USDT** у пользователя @{user['username']}\n"
            f"💰 **Новый баланс:** {new_balance} USDT",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        
        await notify_admins(
            message.bot,
            f"➖ **Админ списал {amount} USDT** у пользователя @{user['username']}\n"
            f"📊 **Новый баланс:** {new_balance} USDT"
        )
        
        try:
            await message.bot.send_message(
                user["id"],
                f"➖ **С вашего счёта списано {amount} USDT!**\n\n"
                f"📊 **Ваш баланс:** {new_balance} USDT",
                parse_mode="Markdown"
            )
        except:
            pass
        
        await state.clear()
    except:
        await message.answer("❌ **Введите число (цифрами)**", parse_mode="Markdown")

# ========== ИЗМЕНИТЬ БАЛАНС ==========
@admin_router.message(lambda msg: msg.text == "🔧 ИЗМЕНИТЬ БАЛАНС" and is_admin(msg.from_user.id))
async def set_balance_start(message: types.Message, state: FSMContext):
    await message.answer(
        "🔧 **ИЗМЕНЕНИЕ БАЛАНСА**\n\n"
        "Введите **username** пользователя (без @):",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(AdminStates.set_balance_username)

@admin_router.message(AdminStates.set_balance_username)
async def set_balance_user(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    username = message.text.strip().replace("@", "")
    user = get_user_by_username(username)
    
    if not user:
        await message.answer(f"❌ **Пользователь @{username} не найден**\n\nПроверьте username и попробуйте снова:", parse_mode="Markdown")
        return
    
    await state.update_data(username=username)
    await message.answer(
        f"👤 **Пользователь:** @{user['username']}\n"
        f"💰 **Текущий баланс:** {user['balance']} USDT\n\n"
        f"💵 **Введите НОВЫЙ баланс (USDT):**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.set_balance_amount)

@admin_router.message(AdminStates.set_balance_amount)
async def set_balance_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ **Операция отменена**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    try:
        new_balance = float(message.text)
        data = await state.get_data()
        username = data.get("username")
        user = get_user_by_username(username)
        
        if not user:
            await message.answer("❌ **Ошибка: пользователь не найден**", reply_markup=admin_keyboard())
            await state.clear()
            return
        
        old_balance = user['balance']
        update_user_by_username(username, {"balance": new_balance})
        
        await message.answer(
            f"✅ **Баланс изменён** для пользователя @{user['username']}\n"
            f"📊 **Старый баланс:** {old_balance} USDT\n"
            f"📊 **Новый баланс:** {new_balance} USDT",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        
        await notify_admins(
            message.bot,
            f"🔧 **Админ изменил баланс** пользователя @{user['username']}\n"
            f"📊 **{old_balance} USDT → {new_balance} USDT**"
        )
        
        try:
            await message.bot.send_message(
                user["id"],
                f"🔧 **Ваш баланс изменён!**\n\n"
                f"📊 **Старый баланс:** {old_balance} USDT\n"
                f"📊 **Новый баланс:** {new_balance} USDT",
                parse_mode="Markdown"
            )
        except:
            pass
        
        await state.clear()
    except:
        await message.answer("❌ **Введите число (цифрами)**", parse_mode="Markdown")

# ========== ПРОСМОТР ПОЛЬЗОВАТЕЛЯ ==========
@admin_router.message(lambda msg: msg.text == "📊 ПРОСМОТР ПОЛЬЗОВАТЕЛЯ" and is_admin(msg.from_user.id))
async def view_user_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📊 **ПРОСМОТР ПОЛЬЗОВАТЕЛЯ**\n\n"
        "Введите **username** пользователя (без @):",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(AdminStates.view_user_username)

@admin_router.message(AdminStates.view_user_username)
async def view_user_result(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    username = message.text.strip().replace("@", "")
    user = get_user_by_username(username)
    
    if not user:
        await message.answer(f"❌ **Пользователь @{username} не найден**", parse_mode="Markdown")
        await state.clear()
        return
    
    rating_list = get_rating_list()
    rating_place = 0
    for i, u in enumerate(rating_list, 1):
        if u["id"] == user["id"]:
            rating_place = i
            break
    
    avg_score = 0
    if user.get("rating_count", 0) > 0:
        avg_score = user.get("rating_score", 0) / user.get("rating_count", 0)
    
    stars = "⭐" * round(avg_score) if avg_score > 0 else "нет"
    
    withdraws = load_withdraws()
    user_withdraws = [w for w in withdraws if w["user_id"] == user["id"]]
    
    text = (
        f"📊 **ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ**\n\n"
        f"👤 **Username:** @{user['username'] or 'нет'}\n"
        f"🆔 **ID:** {user['id']}\n"
        f"💰 **Баланс:** {user['balance']} USDT\n"
        f"📤 **Выведено всего:** {user['total_withdrawn']} USDT\n"
        f"🏆 **Рейтинг:** {rating_place if rating_place > 0 else '0'}\n"
        f"⭐ **Средняя оценка:** {avg_score:.1f}/5 {stars}\n"
        f"📊 **Отзывов оставлено:** {user.get('rating_count', 0)}\n"
        f"📜 **Заявок на вывод:** {len(user_withdraws)}\n"
        f"📅 **Дата регистрации:** {user['joined'][:19]}"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=admin_keyboard())
    await state.clear()

# ========== ЗАЯВКИ НА ВЫВОД ==========
@admin_router.message(lambda msg: msg.text == "✅ ЗАЯВКИ НА ВЫВОД" and is_admin(msg.from_user.id))
async def list_withdraws(message: types.Message):
    withdraws = load_withdraws()
    pending = [w for w in withdraws if w.get("status") == "pending"]
    
    if not pending:
        await message.answer("📭 **Нет активных заявок на вывод**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    for w in pending:
        text = (
            f"💰 **ЗАЯВКА НА ВЫВОД**\n\n"
            f"👤 **От:** @{w.get('username') or 'нет'} (ID: {w['user_id']})\n"
            f"💵 **Сумма:** {w['amount']} USDT\n"
            f"💳 **Способ:** {w['method']}\n"
            f"📝 **Реквизиты:** {w['details']}\n"
            f"📅 **Дата:** {w['created_at'][:19]}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=withdraw_action_keyboard(w["id"]))

@admin_router.callback_query(lambda c: c.data.startswith("approve_withdraw_"))
async def approve_withdraw(callback: types.CallbackQuery):
    wid = int(callback.data.split("_")[-1])
    withdraws = load_withdraws()
    
    for w in withdraws:
        if w["id"] == wid:
            w["status"] = "approved"
            save_withdraws(withdraws)
            
            user = get_user_by_id(w["user_id"])
            if user:
                new_balance = user["balance"] - w["amount"]
                new_total = user.get("total_withdrawn", 0) + w["amount"]
                update_user_by_id(w["user_id"], {"balance": new_balance, "total_withdrawn": new_total})
                
                try:
                    await callback.bot.send_message(
                        w["user_id"],
                        f"✅ **ВАША ЗАЯВКА НА ВЫВОД ОДОБРЕНА!**\n\n"
                        f"💵 **Сумма:** {w['amount']} USDT\n"
                        f"💳 **Способ:** {w['method']}\n\n"
                        f"💰 **Средства будут отправлены в ближайшее время.**\n"
                        f"📊 **Новый баланс:** {new_balance} USDT",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                
                await notify_admins(
                    callback.bot,
                    f"✅ **Заявка на вывод одобрена!**\n"
                    f"👤 **Пользователь:** @{user['username'] or 'нет'}\n"
                    f"💵 **Сумма:** {w['amount']} USDT"
                )
            
            await callback.message.edit_text(f"✅ {callback.message.text}\n\n**СТАТУС: ОДОБРЕНО**")
            break
    
    await callback.answer()

@admin_router.callback_query(lambda c: c.data.startswith("reject_withdraw_"))
async def reject_withdraw(callback: types.CallbackQuery):
    wid = int(callback.data.split("_")[-1])
    withdraws = load_withdraws()
    
    for w in withdraws:
        if w["id"] == wid:
            w["status"] = "rejected"
            save_withdraws(withdraws)
            
            try:
                await callback.bot.send_message(
                    w["user_id"],
                    f"❌ **ВАША ЗАЯВКА НА ВЫВОД ОТКЛОНЕНА!**\n\n"
                    f"💵 **Сумма:** {w['amount']} USDT\n\n"
                    f"📞 **Обратитесь в поддержку для уточнения причины.**",
                    parse_mode="Markdown"
                )
            except:
                pass
            
            await notify_admins(
                callback.bot,
                f"❌ **Заявка на вывод отклонена!**\n"
                f"👤 **Пользователь:** @{w.get('username') or 'нет'}\n"
                f"💵 **Сумма:** {w['amount']} USDT"
            )
            
            await callback.message.edit_text(f"❌ {callback.message.text}\n\n**СТАТУС: ОТКЛОНЕНО**")
            break
    
    await callback.answer()

# ========== УПРАВЛЕНИЕ РЕЙТИНГОМ ==========
@admin_router.message(lambda msg: msg.text == "⭐ УПРАВЛЕНИЕ РЕЙТИНГОМ" and is_admin(msg.from_user.id))
async def set_rating_start(message: types.Message, state: FSMContext):
    await message.answer(
        "⭐ **УСТАНОВКА РЕЙТИНГА**\n\n"
        "Введите **username** пользователя (без @):\n\n"
        "ℹ️ Рейтинг — это место в топе (1, 2, 3...).\n"
        "0 — пользователь не в рейтинге.",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(AdminStates.set_rating_username)

@admin_router.message(AdminStates.set_rating_username)
async def set_rating_user(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    username = message.text.strip().replace("@", "")
    user = get_user_by_username(username)
    
    if not user:
        await message.answer(f"❌ **Пользователь @{username} не найден**\n\nПроверьте username и попробуйте снова:", parse_mode="Markdown")
        return
    
    await state.update_data(username=username)
    await message.answer(
        f"👤 **Пользователь:** @{user['username']}\n"
        f"🏆 **Текущий рейтинг:** {user.get('rating', 0)}\n\n"
        f"⭐ **Введите новое место в рейтинге (число, 0 = не в рейтинге):**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.set_rating_value)

@admin_router.message(AdminStates.set_rating_value)
async def set_rating_value(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ **Операция отменена**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    try:
        rating = int(message.text)
        data = await state.get_data()
        username = data.get("username")
        user = get_user_by_username(username)
        
        if not user:
            await message.answer("❌ **Ошибка: пользователь не найден**", reply_markup=admin_keyboard())
            await state.clear()
            return
        
        update_user_by_username(username, {"rating": rating})
        
        await message.answer(
            f"✅ **Рейтинг обновлён** для пользователя @{user['username']}\n"
            f"🏆 **Новое место:** {rating if rating > 0 else 'не в рейтинге'}",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        
        await notify_admins(
            callback.bot,
            f"⭐ **Админ обновил рейтинг** пользователя @{user['username']}\n"
            f"🏆 **Новое место:** {rating if rating > 0 else 'не в рейтинге'}"
        )
        
        await state.clear()
    except:
        await message.answer("❌ **Введите число (цифрами)**", parse_mode="Markdown")

# ========== СПИСОК ОТЗЫВОВ ==========
@admin_router.message(lambda msg: msg.text == "📋 СПИСОК ОТЗЫВОВ" and is_admin(msg.from_user.id))
async def list_reviews(message: types.Message):
    reviews = load_reviews()
    if not reviews:
        await message.answer("📭 **Нет отзывов**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    reviews.reverse()
    for r in reviews[:20]:
        stars = "⭐" * r["rating"]
        text = (
            f"⭐ **ОТЗЫВ**\n\n"
            f"👤 **От:** {'Аноним' if r.get('is_anonymous') else f'@{r.get(\"username\") or \"нет\"}'}\n"
            f"⭐ **Оценка:** {r['rating']}/5 {stars}\n"
        )
        if r.get("comment"):
            text += f"💬 **Комментарий:** {r['comment']}\n"
        text += f"📅 **Дата:** {r['created_at'][:19]}"
        await message.answer(text, parse_mode="Markdown")
    
    await message.answer("📊 **Показаны последние 20 отзывов**", reply_markup=admin_keyboard(), parse_mode="Markdown")

# ========== РАССЫЛКА ==========
@admin_router.message(lambda msg: msg.text == "📢 РАССЫЛКА" and is_admin(msg.from_user.id))
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📢 **РАССЫЛКА**\n\n"
        "Введите текст для рассылки всем пользователям:",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(AdminStates.broadcast_text)

@admin_router.message(AdminStates.broadcast_text)
async def broadcast_text(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    await state.update_data(text=message.text)
    await message.answer(
        f"📢 **Текст рассылки:**\n\n{message.text}\n\n"
        f"✅ **Отправить?**",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="✅ Да"), types.KeyboardButton(text="❌ Нет")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.broadcast_confirm)

@admin_router.message(AdminStates.broadcast_confirm)
async def broadcast_confirm(message: types.Message, state: FSMContext):
    if message.text == "❌ Нет":
        await state.clear()
        await message.answer("❌ **Рассылка отменена**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    if message.text == "✅ Да":
        data = await state.get_data()
        text = data.get("text", "")
        
        await message.answer("📢 **Начинаю рассылку...**", reply_markup=admin_keyboard())
        await notify_all_users(message.bot, f"📢 **РАССЫЛКА ОТ АДМИНИСТРАЦИИ**\n\n{text}")
        await message.answer("✅ **Рассылка завершена!**", parse_mode="Markdown")
        await state.clear()

# ========== БАН/РАЗБАН ==========
@admin_router.message(lambda msg: msg.text == "👥 БАН/РАЗБАН" and is_admin(msg.from_user.id))
async def ban_menu(message: types.Message):
    kb = [
        [types.KeyboardButton(text="🔨 Забанить")],
        [types.KeyboardButton(text="🔓 Разбанить")],
        [types.KeyboardButton(text="🔙 Назад")]
    ]
    await message.answer("👥 **УПРАВЛЕНИЕ БАНАМИ**\n\nВыберите действие:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode="Markdown")

@admin_router.message(lambda msg: msg.text == "🔨 Забанить" and is_admin(msg.from_user.id))
async def ban_start(message: types.Message, state: FSMContext):
    await message.answer(
        "🔨 **ЗАБАНИТЬ ПОЛЬЗОВАТЕЛЯ**\n\n"
        "Введите **username** пользователя (без @):",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(AdminStates.ban_username)

@admin_router.message(AdminStates.ban_username)
async def ban_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    username = message.text.strip().replace("@", "")
    user = get_user_by_username(username)
    
    if not user:
        await message.answer(f"❌ **Пользователь @{username} не найден**", parse_mode="Markdown")
        await state.clear()
        return
    
    banned = load_banned()
    if user["id"] not in banned:
        banned.append(user["id"])
        save_banned(banned)
        await message.answer(f"✅ **Пользователь @{username} ЗАБАНЕН**", parse_mode="Markdown", reply_markup=admin_keyboard())
        
        await notify_admins(message.bot, f"🔨 **Админ забанил пользователя @{username}**")
        
        try:
            await message.bot.send_message(user["id"], "❌ **Вы были забанены администратором.**", parse_mode="Markdown")
        except:
            pass
    else:
        await message.answer(f"⚠️ **Пользователь @{username} уже в бане**", parse_mode="Markdown")
    
    await state.clear()

@admin_router.message(lambda msg: msg.text == "🔓 Разбанить" and is_admin(msg.from_user.id))
async def unban_start(message: types.Message, state: FSMContext):
    await message.answer(
        "🔓 **РАЗБАНИТЬ ПОЛЬЗОВАТЕЛЯ**\n\n"
        "Введите **username** пользователя (без @):",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await state.set_state(AdminStates.unban_username)

@admin_router.message(AdminStates.unban_username)
async def unban_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("👑 **Админ-панель**", reply_markup=admin_keyboard(), parse_mode="Markdown")
        return
    
    username = message.text.strip().replace("@", "")
    user = get_user_by_username(username)
    
    if not user:
        await message.answer(f"❌ **Пользователь @{username} не найден**", parse_mode="Markdown")
        await state.clear()
        return
    
    banned = load_banned()
    if user["id"] in banned:
        banned.remove(user["id"])
        save_banned(banned)
        await message.answer(f"✅ **Пользователь @{username} РАЗБАНЕН**", parse_mode="Markdown", reply_markup=admin_keyboard())
        
        await notify_admins(message.bot, f"🔓 **Админ разбанил пользователя @{username}**")
        
        try:
            await message.bot.send_message(user["id"], "✅ **Вы были разбанены.**", parse_mode="Markdown")
        except:
            pass
    else:
        await message.answer(f"⚠️ **Пользователь @{username} не в бане**", parse_mode="Markdown")
    
    await state.clear()
