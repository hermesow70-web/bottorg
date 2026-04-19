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
            try:
                await message.bot.send_message(uid, "❌ Вы забанены")
            except:
                pass
    except:
        await message.answer("Ошибка!")
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
            try:
                await message.bot.send_message(uid, "✅ Вы разбанены")
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
    await message.answer("Введите позицию:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.add_actual)

@admin_router.message(AdminStates.add_actual)
async def add_actual_save(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    actual = load_actual()
    actual.append(message.text)
    save_actual(actual)
    await message.answer(f"✅ Добавлено: {message.text}")
    await notify_all_users(message.bot, f"📢 АКТУАЛ обновлён!\nДобавлено: {message.text}")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.message(lambda msg: msg.text == "❌ Удалить" and is_admin(msg.from_user.id))
async def delete_actual_start(message: types.Message, state: FSMContext):
    actual = load_actual()
    if not actual:
        await message.answer("Список пуст")
        return
    text = "Список:\n" + "\n".join(f"{i+1}. {item}" for i, item in enumerate(actual))
    await message.answer(text + "\n\nВведите номер:", reply_markup=back_to_admin())
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
            await notify_all_users(message.bot, f"📢 АКТУАЛ обновлён!\nУдалено: {deleted}")
    except:
        await message.answer("Ошибка!")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.message(lambda msg: msg.text == "📝 Изменить всё" and is_admin(msg.from_user.id))
async def edit_actual_start(message: types.Message, state: FSMContext):
    await message.answer("Введите новый список (каждый с новой строки):", reply_markup=back_to_admin())
    await state.set_state(AdminStates.edit_actual)

@admin_router.message(AdminStates.edit_actual)
async def edit_actual_save(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    new_list = [x.strip() for x in message.text.split("\n") if x.strip()]
    save_actual(new_list)
    await message.answer(f"✅ Обновлено {len(new_list)} позиций")
    await notify_all_users(message.bot, "📢 АКТУАЛ список обновлён!")
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
    text = "Пользователи (последние 20):\n\n"
    for u in users[-20:]:
        status = "🔴 БАН" if u["id"] in banned else "🟢 АКТ"
        text += f"{status} {u['first_name']} (@{u['username'] or 'нет'}) - ID: {u['id']}\n"
    await message.answer(text, reply_markup=admin_keyboard())

@admin_router.message(lambda msg: msg.text == "📊 СТАТИСТИКА" and is_admin(msg.from_user.id))
async def statistics(message: types.Message):
    users = load_users()
    banned = load_banned()
    orders = load_orders()
    supports = load_supports()
    actual = load_actual()
    await message.answer(
        f"📊 Статистика:\n\n👥 Пользователей: {len(users)}\n🔴 Забанено: {len(banned)}\n📦 Заявок: {len(orders)}\n🆘 Обращений: {len(supports)}\n📌 В актуале: {len(actual)}",
        reply_markup=admin_keyboard()
    )
    delete_old_requests(30)

@admin_router.message(lambda msg: msg.text == "📦 СПИСОК ЗАЯВОК" and is_admin(msg.from_user.id))
async def list_orders(message: types.Message):
    orders = load_orders()
    if not orders:
        await message.answer("Нет заявок")
        return
    for o in orders[-10:]:
        await message.answer(
            f"Заявка #{o['id']}\nОт: @{o.get('username') or 'нет'}\nТовар: {o.get('product')}\n{o.get('description')[:100]}",
            reply_markup=order_action_keyboard(o["id"])
        )

@admin_router.message(lambda msg: msg.text == "📋 СПИСОК ЖАЛОБ" and is_admin(msg.from_user.id))
async def list_supports(message: types.Message):
    supports = load_supports()
    if not supports:
        await message.answer("Нет обращений")
        return
    for s in supports[-10:]:
        await message.answer(
            f"Обращение #{s['id']}\nОт: @{s.get('username') or 'нет'}\n{s.get('text')[:100]}",
            reply_markup=support_action_keyboard(s["id"])
        )

# ========== РАССЫЛКА ==========
@admin_router.message(lambda msg: msg.text == "📢 РАССЫЛКА" and is_admin(msg.from_user.id))
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer("Введите текст рассылки:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.broadcast_text)

@admin_router.message(AdminStates.broadcast_text)
async def broadcast_text(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_keyboard())
        return
    await state.update_data(text=message.text)
    await message.answer(f"Текст:\n{message.text}\n\nОтправить? (✅ Да / ❌ Нет)", reply_markup=types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="✅ Да"), types.KeyboardButton(text="❌ Нет")]], resize_keyboard=True))
    await state.set_state(AdminStates.broadcast_confirm)

@admin_router.message(AdminStates.broadcast_confirm)
async def broadcast_confirm(message: types.Message, state: FSMContext):
    if message.text == "❌ Нет":
        await state.clear()
        await message.answer("Отменено", reply_markup=admin_keyboard())
        return
    if message.text == "✅ Да":
        data = await state.get_data()
        await message.answer("Начинаю рассылку...")
        await notify_all_users(message.bot, data.get("text", ""))
        await message.answer("✅ Рассылка завершена!", reply_markup=admin_keyboard())
        await state.clear()

# ========== ПОИСК ==========
@admin_router.message(lambda msg: msg.text == "🔍 ПОИСК" and is_admin(msg.from_user.id))
async def search_menu(message: types.Message):
    await message.answer("Выберите:", reply_markup=search_keyboard())

@admin_router.message(lambda msg: msg.text == "🔍 Поиск по ID" and is_admin(msg.from_user.id))
async def search_id_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ID:", reply_markup=back_to_admin())
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
            await message.answer(f"Найден: {user['first_name']} (@{user['username'] or 'нет'})\nID: {user['id']}\nДата: {user['joined'][:19]}")
        else:
            await message.answer("Не найден")
    except:
        await message.answer("Ошибка!")
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
    user = get_user_by_username(message.text.strip())
    if user:
        await message.answer(f"Найден: {user['first_name']} (@{user['username']})\nID: {user['id']}")
    else:
        await message.answer("Не найден")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

# ========== CALLBACK'и ==========
@admin_router.callback_query(lambda c: c.data.startswith("accept_order_"))
async def accept_order(callback: types.CallbackQuery):
    oid = int(callback.data.split("_")[-1])
    orders = load_orders()
    for o in orders:
        if o["id"] == oid:
            o["status"] = "accepted"
            save_orders(orders)
            await callback.answer("Принято!")
            try:
                await callback.bot.send_message(o["user_id"], "✅ Заявка принята! Админ свяжется")
            except:
                pass
            break

@admin_router.callback_query(lambda c: c.data.startswith("reject_order_"))
async def reject_start(callback: types.CallbackQuery, state: FSMContext):
    oid = int(callback.data.split("_")[-1])
    await state.update_data(reject_id=oid)
    await callback.message.answer("Причина отклонения:")
    await state.set_state(AdminStates.reject_order)
    await callback.answer()

@admin_router.message(AdminStates.reject_order)
async def reject_execute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    oid = data.get("reject_id")
    reason = message.text
    orders = load_orders()
    for o in orders:
        if o["id"] == oid:
            o["status"] = "rejected"
            save_orders(orders)
            try:
                await message.bot.send_message(o["user_id"], f"❌ Заявка отклонена!\nПричина: {reason}")
            except:
                pass
            break
    await state.clear()
    await message.answer("Отклонено", reply_markup=admin_keyboard())

@admin_router.callback_query(lambda c: c.data.startswith("reply_order_"))
async def reply_order_start(callback: types.CallbackQuery, state: FSMContext):
    oid = int(callback.data.split("_")[-1])
    orders = load_orders()
    for o in orders:
        if o["id"] == oid:
            await state.update_data(reply_user=o["user_id"])
            await callback.message.answer("Введите ответ:")
            await state.set_state(AdminStates.reply_order_msg)
            break
    await callback.answer()

@admin_router.message(AdminStates.reply_order_msg)
async def reply_order_execute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("reply_user")
    try:
        await message.bot.send_message(uid, f"📩 Ответ админа:\n{message.text}")
        await message.answer("✅ Отправлено!")
    except:
        await message.answer("Ошибка")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.callback_query(lambda c: c.data.startswith("reply_support_"))
async def reply_support_start(callback: types.CallbackQuery, state: FSMContext):
    sid = int(callback.data.split("_")[-1])
    supports = load_supports()
    for s in supports:
        if s["id"] == sid:
            await state.update_data(reply_user=s["user_id"], reply_id=sid)
            await callback.message.answer("Введите ответ:")
            await state.set_state(AdminStates.reply_support_msg)
            break
    await callback.answer()

@admin_router.message(AdminStates.reply_support_msg)
async def reply_support_execute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("reply_user")
    sid = data.get("reply_id")
    try:
        await message.bot.send_message(uid, f"📩 Ответ админа:\n{message.text}")
        supports = load_supports()
        supports = [s for s in supports if s.get("id") != sid]
        save_supports(supports)
        await message.answer("✅ Отправлено и удалено!")
    except:
        await message.answer("Ошибка")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_keyboard())

@admin_router.callback_query(lambda c: c.data.startswith("delete_support_"))
async def delete_support(callback: types.CallbackQuery):
    sid = int(callback.data.split("_")[-1])
    supports = load_supports()
    supports = [s for s in supports if s.get("id") != sid]
    save_supports(supports)
    await callback.answer("Удалено!")
