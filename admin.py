from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import (
    load_users, load_actual, save_actual, load_banned, save_banned,
    load_supports, save_supports, load_orders, save_orders,
    get_user_by_id, get_user_by_username, delete_old_requests
)
from keyboards import admin_keyboard, back_to_admin, order_action_keyboard, support_action_keyboard, search_keyboard, main_keyboard
from utils import notify_all_users, notify_admins
from config import ADMIN_IDS

admin_router = Router()

# Состояния
class AdminStates(StatesGroup):
    add_actual = State()
    delete_actual = State()
    edit_actual = State()
    broadcast_text = State()
    broadcast_confirm = State()
    ban_user = State()
    unban_user = State()
    reply_support_msg = State()
    reply_order_msg = State()
    reject_order = State()
    search_user = State()
    search_username = State()

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ========== НАВИГАЦИЯ ==========
@admin_router.message(lambda msg: msg.text == "🔙 Назад в админку" and is_admin(msg.from_user.id))
async def back_to_admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.message(lambda msg: msg.text == "🔙 ВЫЙТИ ИЗ АДМИНКИ" and is_admin(msg.from_user.id))
async def exit_admin(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Вы вышли", reply_markup=main_keyboard())

# ========== БАН/РАЗБАН ==========
@admin_router.message(lambda msg: msg.text == "👥 БАН/РАЗБАН" and is_admin(msg.from_user.id))
async def ban_menu(message: types.Message):
    kb = [[types.KeyboardButton(text="🔨 Забанить")], [types.KeyboardButton(text="🔓 Разбанить")], [types.KeyboardButton(text="🔙 Назад в админку")]]
    await message.answer("Выберите:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@admin_router.message(lambda msg: msg.text == "🔨 Забанить" and is_admin(msg.from_user.id))
async def ban_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ID:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.ban_user)

@admin_router.message(AdminStates.ban_user)
async def ban_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    try:
        uid = int(message.text)
        banned = load_banned()
        if uid not in banned:
            banned.append(uid)
            save_banned(banned)
            await message.answer(f"✅ Забанен {uid}")
            await notify_admins(message.bot, f"⚠️ Пользователь {uid} был забанен")
            try:
                await message.bot.send_message(uid, "❌ Вы забанены администратором.")
            except:
                pass
    except:
        await message.answer("Ошибка! Введите ID цифрами")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.message(lambda msg: msg.text == "🔓 Разбанить" and is_admin(msg.from_user.id))
async def unban_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ID:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.unban_user)

@admin_router.message(AdminStates.unban_user)
async def unban_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    try:
        uid = int(message.text)
        banned = load_banned()
        if uid in banned:
            banned.remove(uid)
            save_banned(banned)
            await message.answer(f"✅ Разбанен {uid}")
            await notify_admins(message.bot, f"✅ Пользователь {uid} был разбанен")
            try:
                await message.bot.send_message(uid, "✅ Вы разбанены.")
            except:
                pass
    except:
        await message.answer("Ошибка!")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

# ========== УПРАВЛЕНИЕ АКТУАЛ ==========
@admin_router.message(lambda msg: msg.text == "📌 УПРАВЛЕНИЕ АКТУАЛ" and is_admin(msg.from_user.id))
async def actual_admin(message: types.Message):
    kb = [[types.KeyboardButton(text="➕ Добавить")], [types.KeyboardButton(text="❌ Удалить")], [types.KeyboardButton(text="📝 Изменить всё")], [types.KeyboardButton(text="🔙 Назад в админку")]]
    await message.answer("Управление:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@admin_router.message(lambda msg: msg.text == "➕ Добавить" and is_admin(msg.from_user.id))
async def add_actual_start(message: types.Message, state: FSMContext):
    await message.answer("Введите новую позицию (можно несколько, разделяя переносом строки):", reply_markup=back_to_admin())
    await state.set_state(AdminStates.add_actual)

@admin_router.message(AdminStates.add_actual)
async def add_actual_save(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    actual = load_actual()
    new_items = [item.strip() for item in message.text.split("\n") if item.strip()]
    actual.extend(new_items)
    save_actual(actual)
    await message.answer(f"✅ Добавлено {len(new_items)} позиций")
    await notify_all_users(message.bot, f"📢 **АКТУАЛ список обновлён!**\n\nДобавлено:\n" + "\n".join(f"• {item}" for item in new_items))
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.message(lambda msg: msg.text == "❌ Удалить" and is_admin(msg.from_user.id))
async def delete_actual_start(message: types.Message, state: FSMContext):
    actual = load_actual()
    if not actual:
        await message.answer("Список пуст")
        return
    text = "📋 Текущий список:\n" + "\n".join(f"{i+1}. {item}" for i, item in enumerate(actual))
    await message.answer(text + "\n\nВведите номер для удаления:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.delete_actual)

@admin_router.message(AdminStates.delete_actual)
async def delete_actual_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    try:
        num = int(message.text) - 1
        actual = load_actual()
        if 0 <= num < len(actual):
            deleted = actual.pop(num)
            save_actual(actual)
            await message.answer(f"✅ Удалено: {deleted}")
            await notify_all_users(message.bot, f"📢 **АКТУАЛ список обновлён!**\n\nУдалено: {deleted}")
    except:
        await message.answer("Ошибка! Введите номер цифрой")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.message(lambda msg: msg.text == "📝 Изменить всё" and is_admin(msg.from_user.id))
async def edit_actual_start(message: types.Message, state: FSMContext):
    await message.answer("Введите новый список целиком (каждая позиция с новой строки):", reply_markup=back_to_admin())
    await state.set_state(AdminStates.edit_actual)

@admin_router.message(AdminStates.edit_actual)
async def edit_actual_save(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    new_list = [x.strip() for x in message.text.split("\n") if x.strip()]
    save_actual(new_list)
    await message.answer(f"✅ Список обновлён ({len(new_list)} позиций)")
    await notify_all_users(message.bot, "📢 **АКТУАЛ список полностью обновлён!**")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

# ========== СПИСКИ ==========
@admin_router.message(lambda msg: msg.text == "👤 СПИСОК ПОЛЬЗОВАТЕЛЕЙ" and is_admin(msg.from_user.id))
async def list_users(message: types.Message):
    users = load_users()
    banned = load_banned()
    if not users:
        await message.answer("Нет пользователей")
        return
    text = "👥 **Список пользователей (последние 20):**\n\n"
    for u in users[-20:]:
        status = "🔴 БАН" if u["id"] in banned else "🟢 АКТИВЕН"
        text += f"{status} {u['first_name']} (@{u['username'] or 'нет'}) - ID: {u['id']}\n"
    await message.answer(text, parse_mode="Markdown", reply_markup=admin_keyboard())

@admin_router.message(lambda msg: msg.text == "📊 СТАТИСТИКА" and is_admin(msg.from_user.id))
async def statistics(message: types.Message):
    users = load_users()
    banned = load_banned()
    orders = load_orders()
    supports = load_supports()
    actual = load_actual()
    
    today = datetime.now().date()
    orders_today = 0
    for o in orders:
        try:
            if datetime.fromisoformat(o["created_at"]).date() == today:
                orders_today += 1
        except:
            pass
    supports_today = 0
    for s in supports:
        try:
            if datetime.fromisoformat(s["created_at"]).date() == today:
                supports_today += 1
        except:
            pass
    
    text = (
        f"📊 **СТАТИСТИКА БОТА**\n\n"
        f"👥 Всего пользователей: {len(users)}\n"
        f"🔴 Забанено: {len(banned)}\n"
        f"🟢 Активных: {len(users) - len(banned)}\n\n"
        f"📦 Всего заявок: {len(orders)}\n"
        f"📦 Заявок за сегодня: {orders_today}\n\n"
        f"🆘 Всего обращений: {len(supports)}\n"
        f"🆘 Обращений за сегодня: {supports_today}\n\n"
        f"📌 Позиций в актуале: {len(actual)}"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=admin_keyboard())
    delete_old_requests(30)

@admin_router.message(lambda msg: msg.text == "📦 СПИСОК ЗАЯВОК" and is_admin(msg.from_user.id))
async def list_orders(message: types.Message):
    orders = load_orders()
    # Показываем только заявки со статусом pending
    pending_orders = [o for o in orders if o.get("status") == "pending"]
    if not pending_orders:
        await message.answer("Нет активных заявок", reply_markup=admin_keyboard())
        return
    
    for o in pending_orders[-10:]:
        text = (
            f"⏳ **Заявка #{o['id']}**\n"
            f"👤 От: @{o.get('username') or 'нет'} (ID: {o['user_id']})\n"
            f"📌 Товар: {o.get('product', 'не указан')}\n"
            f"📝 {o.get('description', '')[:100]}...\n"
            f"📅 {o.get('created_at', '')[:19]}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=order_action_keyboard(o["id"]))

@admin_router.message(lambda msg: msg.text == "📋 СПИСОК ЖАЛОБ" and is_admin(msg.from_user.id))
async def list_supports(message: types.Message):
    supports = load_supports()
    # Показываем только обращения со статусом pending
    pending_supports = [s for s in supports if s.get("status") == "pending"]
    if not pending_supports:
        await message.answer("Нет активных обращений", reply_markup=admin_keyboard())
        return
    
    for s in pending_supports[-10:]:
        text = (
            f"🆘 **Обращение #{s['id']}**\n"
            f"👤 От: @{s.get('username') or 'нет'} (ID: {s['user_id']})\n"
            f"📝 {s.get('text', '')[:100]}...\n"
            f"📅 {s.get('created_at', '')[:19]}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=support_action_keyboard(s["id"]))

# ========== РАССЫЛКА ==========
@admin_router.message(lambda msg: msg.text == "📢 РАССЫЛКА" and is_admin(msg.from_user.id))
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer("📢 Введите текст рассылки:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.broadcast_text)

@admin_router.message(AdminStates.broadcast_text)
async def broadcast_text(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    await state.update_data(text=message.html_text)
    await message.answer(
        f"📢 Текст рассылки:\n\n{message.html_text}\n\nОтправить?",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="✅ Да"), types.KeyboardButton(text="❌ Нет")]], resize_keyboard=True)
    )
    await state.set_state(AdminStates.broadcast_confirm)

@admin_router.message(AdminStates.broadcast_confirm)
async def broadcast_confirm(message: types.Message, state: FSMContext):
    if message.text == "❌ Нет":
        await state.clear()
        await message.answer("Рассылка отменена", reply_markup=admin_keyboard())
        return
    if message.text == "✅ Да":
        data = await state.get_data()
        await message.answer("📢 Начинаю рассылку...")
        await notify_all_users(message.bot, data.get("text", ""))
        await message.answer("✅ Рассылка завершена!", reply_markup=admin_keyboard())
        await state.clear()

# ========== ПОИСК ==========
@admin_router.message(lambda msg: msg.text == "🔍 ПОИСК" and is_admin(msg.from_user.id))
async def search_menu(message: types.Message):
    await message.answer("Выберите тип поиска:", reply_markup=search_keyboard())

@admin_router.message(lambda msg: msg.text == "🔍 Поиск по ID" and is_admin(msg.from_user.id))
async def search_id_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ID пользователя:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.search_user)

@admin_router.message(AdminStates.search_user)
async def search_id_result(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    try:
        uid = int(message.text)
        user = get_user_by_id(uid)
        if user:
            await message.answer(f"👤 **Найден пользователь:**\n\nИмя: {user['first_name']}\nUsername: @{user['username'] or 'нет'}\nID: {user['id']}\nДата регистрации: {user['joined'][:19]}")
        else:
            await message.answer("Пользователь не найден")
    except:
        await message.answer("Ошибка! Введите ID цифрами")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.message(lambda msg: msg.text == "🔍 Поиск по username" and is_admin(msg.from_user.id))
async def search_username_start(message: types.Message, state: FSMContext):
    await message.answer("Введите username (без @):", reply_markup=back_to_admin())
    await state.set_state(AdminStates.search_username)

@admin_router.message(AdminStates.search_username)
async def search_username_result(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    user = get_user_by_username(message.text.strip().replace("@", ""))
    if user:
        await message.answer(f"👤 **Найден пользователь:**\n\nИмя: {user['first_name']}\nUsername: @{user['username'] or 'нет'}\nID: {user['id']}")
    else:
        await message.answer("Пользователь не найден")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

# ========== CALLBACK'и для ЗАЯВОК (удаляют из списка) ==========
@admin_router.callback_query(lambda c: c.data.startswith("accept_order_"))
async def accept_order(callback: types.CallbackQuery):
    oid = int(callback.data.split("_")[-1])
    orders = load_orders()
    new_orders = []
    user_id = None
    
    for o in orders:
        if o["id"] == oid:
            user_id = o["user_id"]
            await callback.answer("✅ Заявка принята и удалена из списка!")
            try:
                await callback.bot.send_message(user_id, "✅ **Ваша заявка принята!**\n\nАдминистратор свяжется с вами в ближайшее время.", parse_mode="Markdown")
            except:
                pass
        else:
            new_orders.append(o)
    
    save_orders(new_orders)
    await callback.message.edit_text(f"✅ {callback.message.text}\n\n[ЗАЯВКА ПРИНЯТА И УДАЛЕНА]")

@admin_router.callback_query(lambda c: c.data.startswith("reject_order_"))
async def reject_start(callback: types.CallbackQuery, state: FSMContext):
    oid = int(callback.data.split("_")[-1])
    await state.update_data(reject_id=oid)
    await callback.message.answer("Введите причину отклонения:")
    await state.set_state(AdminStates.reject_order)
    await callback.answer()

@admin_router.message(AdminStates.reject_order)
async def reject_execute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    oid = data.get("reject_id")
    reason = message.text
    
    orders = load_orders()
    new_orders = []
    user_id = None
    
    for o in orders:
        if o["id"] == oid:
            user_id = o["user_id"]
            try:
                await message.bot.send_message(user_id, f"❌ **Ваша заявка отклонена!**\n\nПричина: {reason}\n\nЕсли вы не согласны, обратитесь в поддержку.", parse_mode="Markdown")
            except:
                pass
        else:
            new_orders.append(o)
    
    save_orders(new_orders)
    await state.clear()
    await message.answer(f"✅ Заявка #{oid} отклонена и удалена из списка.", reply_markup=admin_keyboard())

@admin_router.callback_query(lambda c: c.data.startswith("reply_order_"))
async def reply_order_start(callback: types.CallbackQuery, state: FSMContext):
    oid = int(callback.data.split("_")[-1])
    orders = load_orders()
    for o in orders:
        if o["id"] == oid:
            await state.update_data(reply_user=o["user_id"], reply_id=oid)
            await callback.message.answer("Введите ответ пользователю (анонимно):")
            await state.set_state(AdminStates.reply_order_msg)
            break
    await callback.answer()

@admin_router.message(AdminStates.reply_order_msg)
async def reply_order_execute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("reply_user")
    oid = data.get("reply_id")
    answer = message.text
    
    # Удаляем заявку после ответа
    orders = load_orders()
    new_orders = [o for o in orders if o["id"] != oid]
    save_orders(new_orders)
    
    try:
        await message.bot.send_message(uid, f"📩 **Ответ администратора на вашу заявку:**\n\n{answer}\n\nЭто автоматическое сообщение, отвечать на него не нужно.", parse_mode="Markdown")
        await message.answer("✅ Ответ отправлен пользователю! Заявка удалена из списка.")
    except:
        await message.answer("❌ Не удалось отправить ответ")
    
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

# ========== CALLBACK'и для ОБРАЩЕНИЙ (удаляют из списка) ==========
@admin_router.callback_query(lambda c: c.data.startswith("reply_support_"))
async def reply_support_start(callback: types.CallbackQuery, state: FSMContext):
    sid = int(callback.data.split("_")[-1])
    supports = load_supports()
    for s in supports:
        if s["id"] == sid:
            await state.update_data(reply_user=s["user_id"], reply_id=sid)
            await callback.message.answer("Введите ответ пользователю (анонимно):")
            await state.set_state(AdminStates.reply_support_msg)
            break
    await callback.answer()

@admin_router.message(AdminStates.reply_support_msg)
async def reply_support_execute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("reply_user")
    sid = data.get("reply_id")
    answer = message.text
    
    # Удаляем обращение после ответа
    supports = load_supports()
    new_supports = [s for s in supports if s["id"] != sid]
    save_supports(new_supports)
    
    try:
        await message.bot.send_message(uid, f"📩 **Ответ администратора на ваше обращение:**\n\n{answer}\n\nЕсли остались вопросы — пишите снова.", parse_mode="Markdown")
        await message.answer("✅ Ответ отправлен пользователю! Обращение удалено из списка.")
    except:
        await message.answer("❌ Не удалось отправить ответ")
    
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.callback_query(lambda c: c.data.startswith("delete_support_"))
async def delete_support(callback: types.CallbackQuery):
    sid = int(callback.data.split("_")[-1])
    supports = load_supports()
    new_supports = [s for s in supports if s["id"] != sid]
    save_supports(new_supports)
    await callback.answer("Обращение удалено!")
    await callback.message.edit_text(f"🗑 {callback.message.text}")
