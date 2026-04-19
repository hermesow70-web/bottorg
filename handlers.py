import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import (
    load_actual, register_user, load_banned, save_supports, save_orders,
    load_orders as load_orders_db, load_supports as load_supports_db,
    save_actual, save_banned, get_user_by_id, get_user_by_username, delete_old_requests
)
from keyboards import (
    main_keyboard, back_to_user_menu, admin_main_keyboard, back_to_admin,
    order_action_keyboard, support_action_keyboard, search_keyboard
)
from utils import logger, notify_all_users, notify_admins
from config import ADMIN_IDS

# ========== СОСТОЯНИЯ ==========
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

class SupportStates(StatesGroup):
    waiting_for_message = State()

class SellStates(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_description = State()
    waiting_for_confirm = State()

# ========== РОУТЕРЫ ==========
user_router = Router()
admin_router = Router()

# ========== ПРОВЕРКИ ==========
async def check_banned(user_id):
    return user_id in load_banned()

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ========== ПОЛЬЗОВАТЕЛЬСКИЕ ОБРАБОТЧИКИ ==========
@user_router.message(Command("start"))
async def start(message: types.Message):
    await register_user(message.from_user)
    if await check_banned(message.from_user.id):
        await message.answer("❌ Вы забанены.")
        return
    await message.answer(
        "**🔥 Привет, тут ты можешь продать материал и получить хорошие деньги! 🔥**\n\n"
        "ℹ️ Чтобы ознакомиться что мы покупаем в общем, жми на **ИНФО**\n"
        "📌 Хочешь узнать что мы берём на данный момент, жми на **АКТУАЛ**\n"
        "🆘 Для связи с администрацией жми на **ПОДДЕРЖКА**\n\n"
        "💰 Чтобы продать материал — жми **ПРОДАТЬ**",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@user_router.message(lambda msg: msg.text == "🔙 Назад в главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Возвращаюсь в главное меню.", reply_markup=main_keyboard())

@user_router.message(lambda msg: msg.text == "ℹ️ ИНФО")
async def info(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    await message.answer(
        "📢 **Наш канал с информацией:**\nhttps://t.me/+ZAJelSN78aliNzIx",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@user_router.message(lambda msg: msg.text == "📌 АКТУАЛ")
async def actual(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    items = load_actual()
    if not items:
        await message.answer("📋 Список актуальных позиций пуст. Загляните позже!", reply_markup=main_keyboard())
    else:
        text = "📌 **Сейчас мы покупаем:**\n\n" + "\n".join(f"• {item}" for item in items)
        await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard())

@user_router.message(lambda msg: msg.text == "💰 ПРОДАТЬ")
async def sell_start(message: types.Message, state: FSMContext):
    if await check_banned(message.from_user.id):
        return
    items = load_actual()
    if not items:
        await message.answer(
            "❌ **Список актуальных материалов пуст!**\n\nАдминистраторы ещё не добавили позиции. Загляните позже.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return
    actual_list_text = "\n".join(f"• {item}" for item in items)
    await message.answer(
        f"📌 **Список материалов, которые мы покупаем:**\n\n{actual_list_text}\n\n"
        f"✏️ **Введите название материала, который вы хотите продать:**\n\n"
        f"⚠️ Внимание! Продажа возможна только из списка выше.",
        parse_mode="Markdown",
        reply_markup=back_to_user_menu()
    )
    await state.set_state(SellStates.waiting_for_product_name)

@user_router.message(SellStates.waiting_for_product_name)
async def check_product_name(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в главное меню":
        await state.clear()
        await message.answer("Возвращаюсь в главное меню.", reply_markup=main_keyboard())
        return
    product_name = message.text.strip()
    actual_items = load_actual()
    found = None
    for item in actual_items:
        if item.lower() == product_name.lower():
            found = item
            break
    if found:
        await state.update_data(product_name=found)
        await message.answer(
            f"✅ **Материал \"{found}\" найден в списке!**\n\n"
            f"📝 Теперь напишите **подробное описание материала** (количество, состояние, особенности):",
            parse_mode="Markdown",
            reply_markup=back_to_user_menu()
        )
        await state.set_state(SellStates.waiting_for_description)
    else:
        await message.answer(
            f"❌ **Материал \"{product_name}\" не найден в списке АКТУАЛ!**\n\n"
            f"📌 Актуальный список материалов:\n" + "\n".join(f"• {item}" for item in actual_items) + 
            f"\n\n🆘 Если вы уверены, что материал принимается — свяжитесь с администрацией через кнопку **ПОДДЕРЖКА**\n\n"
            f"🔄 Попробуйте снова или нажмите «Назад в главное меню».",
            parse_mode="Markdown",
            reply_markup=back_to_user_menu()
        )

@user_router.message(SellStates.waiting_for_description)
async def get_description(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в главное меню":
        await state.clear()
        await message.answer("Возвращаюсь в главное меню.", reply_markup=main_keyboard())
        return
    description = message.text.strip()
    await state.update_data(description=description)
    user_data = await state.get_data()
    product_name = user_data.get("product_name")
    preview_text = (
        f"📦 **Предпросмотр вашей заявки:**\n\n"
        f"📌 Материал: {product_name}\n"
        f"📝 Описание: {description}\n\n"
        f"✅ Всё верно? Нажмите **ОТПРАВИТЬ**\n"
        f"✏️ Или нажмите **НАЗАД**, чтобы изменить описание."
    )
    kb = [
        [types.KeyboardButton(text="✅ ОТПРАВИТЬ")],
        [types.KeyboardButton(text="✏️ НАЗАД (изменить описание)")],
        [types.KeyboardButton(text="🔙 Назад в главное меню")]
    ]
    await message.answer(
        preview_text,
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.set_state(SellStates.waiting_for_confirm)

@user_router.message(SellStates.waiting_for_confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    product_name = user_data.get("product_name")
    description = user_data.get("description")
    if message.text == "✏️ НАЗАД (изменить описание)":
        await message.answer("📝 Напишите новое описание материала:", reply_markup=back_to_user_menu())
        await state.set_state(SellStates.waiting_for_description)
        return
    if message.text == "🔙 Назад в главное меню":
        await state.clear()
        await message.answer("Возвращаюсь в главное меню.", reply_markup=main_keyboard())
        return
    if message.text == "✅ ОТПРАВИТЬ":
        order_data = {
            "id": int(datetime.now().timestamp()),
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "product": product_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        orders = load_orders_db()
        orders.append(order_data)
        save_orders(orders)
        await notify_admins(
            message.bot,
            f"💰 **НОВАЯ ЗАЯВКА НА ПРОДАЖУ!**\n\n"
            f"👤 От: @{message.from_user.username or 'нет'} (ID: {message.from_user.id})\n"
            f"📌 Материал: {product_name}\n"
            f"📝 Описание: {description}",
            reply_markup=order_action_keyboard(order_data["id"])
        )
        await state.clear()
        await message.answer(
            "✅ **Ваша заявка отправлена!**\n\n"
            f"📌 Материал: {product_name}\n"
            f"Администратор рассмотрит вашу заявку и свяжется с вами в ближайшее время.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

@user_router.message(lambda msg: msg.text == "🆘 ПОДДЕРЖКА")
async def support_start(message: types.Message, state: FSMContext):
    if await check_banned(message.from_user.id):
        return
    await message.answer("✏️ Напишите ваше обращение:", reply_markup=back_to_user_menu())
    await state.set_state(SupportStates.waiting_for_message)

@user_router.message(SupportStates.waiting_for_message)
async def support_send(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в главное меню":
        await state.clear()
        await message.answer("Возвращаюсь в главное меню.", reply_markup=main_keyboard())
        return
    support_data = {
        "id": int(datetime.now().timestamp()),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "text": message.text,
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    supports = load_supports_db()
    supports.append(support_data)
    save_supports(supports)
    await notify_admins(
        message.bot,
        f"🆘 **НОВОЕ ОБРАЩЕНИЕ!**\n"
        f"👤 От: @{message.from_user.username or 'нет'} (ID: {message.from_user.id})\n"
        f"📝 Текст: {message.text}",
        reply_markup=support_action_keyboard(support_data["id"])
    )
    await state.clear()
    await message.answer("✅ Обращение отправлено! Администратор ответит вам в ближайшее время.", reply_markup=main_keyboard())

# ========== АДМИН ОБРАБОТЧИКИ (АНОНИМНЫЕ) ==========
@admin_router.message(lambda msg: msg.text == "🔙 Назад в админку" and is_admin(msg.from_user.id))
async def back_to_admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.message(lambda msg: msg.text == "🔙 ВЫЙТИ ИЗ АДМИНКИ" and is_admin(msg.from_user.id))
async def exit_admin(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выход из админ-панели", reply_markup=main_keyboard())

@admin_router.message(lambda msg: msg.text == "👥 БАН/РАЗБАН" and is_admin(msg.from_user.id))
async def ban_menu(message: types.Message):
    kb = [
        [types.KeyboardButton(text="🔨 Забанить")],
        [types.KeyboardButton(text="🔓 Разбанить")],
        [types.KeyboardButton(text="🔙 Назад в админку")]
    ]
    await message.answer("Выберите действие:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@admin_router.message(lambda msg: msg.text == "🔨 Забанить" and is_admin(msg.from_user.id))
async def ban_user_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ID пользователя для бана:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.ban_user)

@admin_router.message(AdminStates.ban_user)
async def ban_user_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_main_keyboard())
        return
    try:
        user_id = int(message.text)
        banned = load_banned()
        if user_id not in banned:
            banned.append(user_id)
            save_banned(banned)
            await message.answer(f"✅ Пользователь {user_id} забанен")
            await notify_admins(message.bot, f"⚠️ Пользователь {user_id} был забанен")
            try:
                await message.bot.send_message(user_id, "❌ Вы были забанены администратором.")
            except:
                pass
        else:
            await message.answer("Пользователь уже в бане")
    except:
        await message.answer("Ошибка! Введите ID цифрами")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.message(lambda msg: msg.text == "🔓 Разбанить" and is_admin(msg.from_user.id))
async def unban_user_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ID пользователя для разбана:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.unban_user)

@admin_router.message(AdminStates.unban_user)
async def unban_user_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_main_keyboard())
        return
    try:
        user_id = int(message.text)
        banned = load_banned()
        if user_id in banned:
            banned.remove(user_id)
            save_banned(banned)
            await message.answer(f"✅ Пользователь {user_id} разбанен")
            await notify_admins(message.bot, f"✅ Пользователь {user_id} был разбанен")
            try:
                await message.bot.send_message(user_id, "✅ Вы были разбанены.")
            except:
                pass
        else:
            await message.answer("Пользователь не в бане")
    except:
        await message.answer("Ошибка! Введите ID цифрами")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.message(lambda msg: msg.text == "📌 УПРАВЛЕНИЕ АКТУАЛ" and is_admin(msg.from_user.id))
async def actual_admin(message: types.Message):
    kb = [
        [types.KeyboardButton(text="➕ Добавить")],
        [types.KeyboardButton(text="❌ Удалить")],
        [types.KeyboardButton(text="📝 Изменить весь список")],
        [types.KeyboardButton(text="🔙 Назад в админку")]
    ]
    await message.answer("Управление актуальным списком:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@admin_router.message(lambda msg: msg.text == "➕ Добавить" and is_admin(msg.from_user.id))
async def add_actual_start(message: types.Message, state: FSMContext):
    await message.answer("Введите новую позицию (можно несколько, разделяя переносом строки):", reply_markup=back_to_admin())
    await state.set_state(AdminStates.add_actual)

@admin_router.message(AdminStates.add_actual)
async def add_actual_save(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_main_keyboard())
        return
    actual = load_actual()
    new_items = [item.strip() for item in message.text.split("\n") if item.strip()]
    actual.extend(new_items)
    save_actual(actual)
    await message.answer(f"✅ Добавлено {len(new_items)} позиций")
    await notify_all_users(message.bot, f"📢 **АКТУАЛ список обновлён!**\n\nДобавлено:\n" + "\n".join(f"• {item}" for item in new_items))
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.message(lambda msg: msg.text == "❌ Удалить" and is_admin(msg.from_user.id))
async def delete_actual_start(message: types.Message, state: FSMContext):
    actual = load_actual()
    if not actual:
        await message.answer("Список пуст.", reply_markup=admin_main_keyboard())
        return
    text = "📋 Текущий список:\n" + "\n".join(f"{i+1}. {item}" for i, item in enumerate(actual))
    await message.answer(text + "\n\nВведите номер позиции для удаления:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.delete_actual)

@admin_router.message(AdminStates.delete_actual)
async def delete_actual_execute(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_main_keyboard())
        return
    try:
        num = int(message.text) - 1
        actual = load_actual()
        if 0 <= num < len(actual):
            deleted = actual.pop(num)
            save_actual(actual)
            await message.answer(f"✅ Удалено: {deleted}")
            await notify_all_users(message.bot, f"📢 **АКТУАЛ список обновлён!**\n\nУдалено: {deleted}")
        else:
            await message.answer("Неверный номер")
    except:
        await message.answer("Введите номер цифрой")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.message(lambda msg: msg.text == "📝 Изменить весь список" and is_admin(msg.from_user.id))
async def edit_actual_start(message: types.Message, state: FSMContext):
    await message.answer("Введите новый список целиком (каждая позиция с новой строки):", reply_markup=back_to_admin())
    await state.set_state(AdminStates.edit_actual)

@admin_router.message(AdminStates.edit_actual)
async def edit_actual_save(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_main_keyboard())
        return
    new_list = [item.strip() for item in message.text.split("\n") if item.strip()]
    save_actual(new_list)
    await message.answer(f"✅ Список обновлён ({len(new_list)} позиций)")
    await notify_all_users(message.bot, "📢 **АКТУАЛ список полностью обновлён!**\n\nНажмите кнопку АКТУАЛ, чтобы посмотреть.")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.message(lambda msg: msg.text == "👤 СПИСОК ПОЛЬЗОВАТЕЛЕЙ" and is_admin(msg.from_user.id))
async def list_users(message: types.Message):
    users = load_users()
    banned = load_banned()
    if not users:
        await message.answer("Нет пользователей", reply_markup=admin_main_keyboard())
        return
    text = "👥 **Список пользователей (последние 20):**\n\n"
    for user in users[-20:]:
        status = "🔴 БАН" if user["id"] in banned else "🟢 АКТИВЕН"
        text += f"• {user['first_name']} (@{user['username'] or 'нет'}) - ID: {user['id']} - {status}\n"
    await message.answer(text, parse_mode="Markdown", reply_markup=admin_main_keyboard())

@admin_router.message(lambda msg: msg.text == "📊 СТАТИСТИКА" and is_admin(msg.from_user.id))
async def statistics(message: types.Message):
    users = load_users()
    banned = load_banned()
    orders = load_orders_db()
    supports = load_supports_db()
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
        "📊 **СТАТИСТИКА БОТА**\n\n"
        f"👥 Всего пользователей: {len(users)}\n"
        f"🔴 Забанено: {len(banned)}\n"
        f"🟢 Активных: {len(users) - len(banned)}\n\n"
        f"📦 Всего заявок: {len(orders)}\n"
        f"📦 Заявок за сегодня: {orders_today}\n\n"
        f"🆘 Всего обращений: {len(supports)}\n"
        f"🆘 Обращений за сегодня: {supports_today}\n\n"
        f"📌 Позиций в актуале: {len(actual)}"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=admin_main_keyboard())
    
    delete_old_requests(30)

@admin_router.message(lambda msg: msg.text == "📦 СПИСОК ЗАЯВОК" and is_admin(msg.from_user.id))
async def list_orders(message: types.Message):
    orders = load_orders_db()
    if not orders:
        await message.answer("Нет заявок", reply_markup=admin_main_keyboard())
        return
    
    for order in orders[-10:]:
        status_emoji = "⏳" if order.get("status") == "pending" else "✅" if order.get("status") == "accepted" else "❌"
        text = (
            f"{status_emoji} **Заявка #{order['id']}**\n"
            f"👤 От: @{order.get('username') or 'нет'} (ID: {order['user_id']})\n"
            f"📌 Материал: {order.get('product', 'не указан')}\n"
            f"📝 {order.get('description', order.get('text', ''))[:100]}...\n"
            f"📅 {order.get('created_at', '')[:19]}\n"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=order_action_keyboard(order["id"]))

@admin_router.message(lambda msg: msg.text == "📋 СПИСОК ЖАЛОБ" and is_admin(msg.from_user.id))
async def list_supports(message: types.Message):
    supports = load_supports_db()
    if not supports:
        await message.answer("Нет обращений", reply_markup=admin_main_keyboard())
        return
    
    for support in supports[-10:]:
        text = (
            f"🆘 **Обращение #{support['id']}**\n"
            f"👤 От: @{support.get('username') or 'нет'} (ID: {support['user_id']})\n"
            f"📝 {support.get('text', '')[:100]}...\n"
            f"📅 {support.get('created_at', '')[:19]}\n"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=support_action_keyboard(support["id"]))

@admin_router.message(lambda msg: msg.text == "📢 РАССЫЛКА" and is_admin(msg.from_user.id))
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📢 **Режим рассылки**\n\nОтправьте текст рассылки:",
        reply_markup=back_to_admin()
    )
    await state.set_state(AdminStates.broadcast_text)

@admin_router.message(AdminStates.broadcast_text)
async def broadcast_get_text(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_main_keyboard())
        return
    
    await state.update_data(broadcast_text=message.html_text)
    
    kb = [
        [types.KeyboardButton(text="✅ Отправить")],
        [types.KeyboardButton(text="❌ Отмена")],
        [types.KeyboardButton(text="🔙 Назад в админку")]
    ]
    await message.answer(
        f"📢 Текст рассылки:\n\n{message.html_text}\n\nНажмите 'Отправить' для подтверждения.",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.set_state(AdminStates.broadcast_confirm)

@admin_router.message(AdminStates.broadcast_confirm)
async def broadcast_confirm(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Рассылка отменена.", reply_markup=admin_main_keyboard())
        return
    elif message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_main_keyboard())
        return
    elif message.text == "✅ Отправить":
        data = await state.get_data()
        text = data.get("broadcast_text", "")
        
        await message.answer("📢 Начинаю рассылку...")
        await notify_all_users(message.bot, text)
        await message.answer("✅ Рассылка завершена!", reply_markup=admin_main_keyboard())
        await state.clear()

@admin_router.message(lambda msg: msg.text == "🔍 ПОИСК" and is_admin(msg.from_user.id))
async def search_menu(message: types.Message):
    await message.answer("Выберите тип поиска:", reply_markup=search_keyboard())

@admin_router.message(lambda msg: msg.text == "🔍 Поиск по ID" and is_admin(msg.from_user.id))
async def search_by_id_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ID пользователя:", reply_markup=back_to_admin())
    await state.set_state(AdminStates.search_user)

@admin_router.message(AdminStates.search_user)
async def search_by_id_result(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_main_keyboard())
        return
    try:
        user_id = int(message.text)
        user = get_user_by_id(user_id)
        banned = load_banned()
        orders = [o for o in load_orders_db() if o.get("user_id") == user_id]
        supports = [s for s in load_supports_db() if s.get("user_id") == user_id]
        
        if user:
            status = "🔴 БАН" if user_id in banned else "🟢 АКТИВЕН"
            text = (
                f"👤 **Найден пользователь:**\n\n"
                f"Имя: {user['first_name']}\n"
                f"Username: @{user['username'] or 'нет'}\n"
                f"ID: {user['id']}\n"
                f"Статус: {status}\n"
                f"Дата регистрации: {user['joined'][:19]}\n\n"
                f"📦 Заявок: {len(orders)}\n"
                f"🆘 Обращений: {len(supports)}"
            )
            await message.answer(text, parse_mode="Markdown")
        else:
            await message.answer("Пользователь не найден")
    except:
        await message.answer("Ошибка! Введите ID цифрами")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.message(lambda msg: msg.text == "🔍 Поиск по username" and is_admin(msg.from_user.id))
async def search_by_username_start(message: types.Message, state: FSMContext):
    await message.answer("Введите username пользователя (без @):", reply_markup=back_to_admin())
    await state.set_state(AdminStates.search_username)

@admin_router.message(AdminStates.search_username)
async def search_by_username_result(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в админку":
        await state.clear()
        await message.answer("Админ-панель", reply_markup=admin_main_keyboard())
        return
    username = message.text.strip().replace("@", "")
    user = get_user_by_username(username)
    banned = load_banned()
    
    if user:
        user_id = user["id"]
        orders = [o for o in load_orders_db() if o.get("user_id") == user_id]
        supports = [s for s in load_supports_db() if s.get("user_id") == user_id]
        status = "🔴 БАН" if user_id in banned else "🟢 АКТИВЕН"
        text = (
            f"👤 **Найден пользователь:**\n\n"
            f"Имя: {user['first_name']}\n"
            f"Username: @{user['username'] or 'нет'}\n"
            f"ID: {user['id']}\n"
            f"Статус: {status}\n"
            f"Дата регистрации: {user['joined'][:19]}\n\n"
            f"📦 Заявок: {len(orders)}\n"
            f"🆘 Обращений: {len(supports)}"
        )
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.answer("Пользователь не найден")
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

# ========== INLINE CALLBACK'и (АНОНИМНЫЕ) ==========
@admin_router.callback_query(lambda c: c.data.startswith("accept_order_"))
async def accept_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[-1])
    orders = load_orders_db()
    for order in orders:
        if order["id"] == order_id:
            order["status"] = "accepted"
            save_orders(orders)
            await callback.answer("Заявка принята!")
            await callback.message.edit_text(f"✅ {callback.message.text}")
            try:
                await callback.bot.send_message(
                    order["user_id"],
                    f"✅ **Ваша заявка принята!**\n\nАдминистратор свяжется с вами в ближайшее время.",
                    parse_mode="Markdown"
                )
            except:
                pass
            break

@admin_router.callback_query(lambda c: c.data.startswith("reject_order_"))
async def reject_order_start(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[-1])
    await state.update_data(reject_order_id=order_id)
    await callback.message.answer("Введите причину отклонения:")
    await state.set_state(AdminStates.reject_order)
    await callback.answer()

@admin_router.message(AdminStates.reject_order)
async def reject_order_execute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("reject_order_id")
    reason = message.text
    
    orders = load_orders_db()
    for order in orders:
        if order["id"] == order_id:
            order["status"] = "rejected"
            save_orders(orders)
            try:
                await message.bot.send_message(
                    order["user_id"],
                    f"❌ **Ваша заявка отклонена!**\n\nПричина: {reason}\n\nЕсли вы не согласны, обратитесь в поддержку.",
                    parse_mode="Markdown"
                )
            except:
                pass
            await message.answer(f"✅ Заявка #{order_id} отклонена. Причина отправлена пользователю.")
            break
    
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.callback_query(lambda c: c.data.startswith("reply_order_"))
async def reply_order_start(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[-1])
    orders = load_orders_db()
    for order in orders:
        if order["id"] == order_id:
            await state.update_data(reply_user_id=order["user_id"])
            await callback.message.answer("Введите ответ пользователю (анонимно):")
            await state.set_state(AdminStates.reply_order_msg)
            break
    await callback.answer()

@admin_router.message(AdminStates.reply_order_msg)
async def reply_order_execute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_user_id")
    answer = message.text
    
    try:
        await message.bot.send_message(
            user_id,
            f"📩 **Ответ администратора на вашу заявку:**\n\n{answer}\n\nЭто автоматическое сообщение, отвечать на него не нужно.",
            parse_mode="Markdown"
        )
        await message.answer("✅ Ответ отправлен пользователю (анонимно)!")
    except:
        await message.answer("❌ Не удалось отправить ответ (пользователь заблокировал бота)")
    
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.callback_query(lambda c: c.data.startswith("reply_support_"))
async def reply_support_start(callback: types.CallbackQuery, state: FSMContext):
    support_id = int(callback.data.split("_")[-1])
    supports = load_supports_db()
    for support in supports:
        if support["id"] == support_id:
            await state.update_data(reply_support_user_id=support["user_id"], reply_support_id=support_id)
            await callback.message.answer("Введите ответ пользователю (анонимно):")
            await state.set_state(AdminStates.reply_support_msg)
            break
    await callback.answer()

@admin_router.message(AdminStates.reply_support_msg)
async def reply_support_execute(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_support_user_id")
    support_id = data.get("reply_support_id")
    answer = message.text
    
    supports = load_supports_db()
    new_supports = [s for s in supports if s.get("id") != support_id]
    save_supports(new_supports)
    
    try:
        await message.bot.send_message(
            user_id,
            f"📩 **Ответ администратора на ваше обращение:**\n\n{answer}\n\nЕсли остались вопросы — пишите снова.\n\nЭто автоматическое сообщение, отвечать на него не нужно.",
            parse_mode="Markdown"
        )
        await message.answer("✅ Ответ отправлен пользователю (анонимно)! Обращение удалено из списка.")
    except:
        await message.answer("❌ Не удалось отправить ответ (пользователь заблокировал бота)")
    
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_main_keyboard())

@admin_router.callback_query(lambda c: c.data.startswith("delete_support_"))
async def delete_support(callback: types.CallbackQuery):
    support_id = int(callback.data.split("_")[-1])
    supports = load_supports_db()
    new_supports = [s for s in supports if s.get("id") != support_id]
    save_supports(new_supports)
    await callback.answer("Обращение удалено!")
    await callback.message.edit_text(f"🗑 {callback.message.text}")
