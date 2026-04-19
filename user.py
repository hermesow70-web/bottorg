import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import load_actual, register_user, load_banned, save_supports, save_orders, load_orders as load_orders_db, load_supports as load_supports_db
from keyboards import main_keyboard, back_to_user_menu
from utils import notify_admins
from config import ADMIN_IDS

user_router = Router()

# Состояния
class SellStates(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_description = State()
    waiting_for_confirm = State()

class SupportStates(StatesGroup):
    waiting_for_message = State()

async def check_banned(user_id):
    return user_id in load_banned()

@user_router.message(Command("start"))
async def start(message: types.Message):
    await register_user(message.from_user)
    if await check_banned(message.from_user.id):
        await message.answer("❌ Вы забанены.")
        return
    
    await message.answer(
        "**🔥 Привет, тут ты можешь продать материал и получить хорошие деньги! 🔥**\n\n"
        "ℹ️ ИНФО - что мы покупаем\n"
        "📌 АКТУАЛ - что берём сейчас\n"
        "🆘 ПОДДЕРЖКА - связаться с админом\n\n"
        "💰 ПРОДАТЬ - продать материал",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@user_router.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    if message.from_user.id in ADMIN_IDS:
        from keyboards import admin_keyboard
        await message.answer("👑 Админ-панель", reply_markup=admin_keyboard())
    else:
        await message.answer("❌ Нет доступа")

@user_router.message(lambda msg: msg.text == "🔙 Назад в главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=main_keyboard())

@user_router.message(lambda msg: msg.text == "ℹ️ ИНФО")
async def info(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    await message.answer("📢 Канал: https://t.me/+ZAJelSN78aliNzIx", reply_markup=main_keyboard())

@user_router.message(lambda msg: msg.text == "📌 АКТУАЛ")
async def actual(message: types.Message):
    if await check_banned(message.from_user.id):
        return
    items = load_actual()
    if not items:
        await message.answer("Список пуст", reply_markup=main_keyboard())
    else:
        text = "📌 Сейчас покупаем:\n\n" + "\n".join(f"• {item}" for item in items)
        await message.answer(text, reply_markup=main_keyboard())

@user_router.message(lambda msg: msg.text == "💰 ПРОДАТЬ")
async def sell_start(message: types.Message, state: FSMContext):
    if await check_banned(message.from_user.id):
        return
    items = load_actual()
    if not items:
        await message.answer("Список актуальных материалов пуст. Загляните позже!", reply_markup=main_keyboard())
        return
    
    text = "📌 Список материалов:\n" + "\n".join(f"• {item}" for item in items)
    await message.answer(text + "\n\n✏️ Введите название материала:", reply_markup=back_to_user_menu())
    await state.set_state(SellStates.waiting_for_product_name)

@user_router.message(SellStates.waiting_for_product_name)
async def check_product(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в главное меню":
        await state.clear()
        await message.answer("Главное меню", reply_markup=main_keyboard())
        return
    
    actual_items = load_actual()
    found = None
    for item in actual_items:
        if item.lower() == message.text.strip().lower():
            found = item
            break
    
    if found:
        await state.update_data(product=found)
        await message.answer("📝 Введите описание материала:", reply_markup=back_to_user_menu())
        await state.set_state(SellStates.waiting_for_description)
    else:
        await message.answer(
            f"❌ Материал \"{message.text}\" не найден в списке!\n\n📌 Список:\n" + "\n".join(f"• {item}" for item in actual_items) +
            "\n\nПопробуйте снова:",
            reply_markup=back_to_user_menu()
        )

@user_router.message(SellStates.waiting_for_description)
async def get_description(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в главное меню":
        await state.clear()
        await message.answer("Главное меню", reply_markup=main_keyboard())
        return
    
    await state.update_data(description=message.text)
    data = await state.get_data()
    
    kb = [
        [types.KeyboardButton(text="✅ ОТПРАВИТЬ")],
        [types.KeyboardButton(text="✏️ ИЗМЕНИТЬ")],
        [types.KeyboardButton(text="🔙 Назад в главное меню")]
    ]
    await message.answer(
        f"📦 **Предпросмотр заявки:**\n\n📌 Товар: {data['product']}\n📝 Описание: {data['description']}\n\n✅ Отправить?",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.set_state(SellStates.waiting_for_confirm)

@user_router.message(SellStates.waiting_for_confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад в главное меню":
        await state.clear()
        await message.answer("Главное меню", reply_markup=main_keyboard())
        return
    if message.text == "✏️ ИЗМЕНИТЬ":
        await message.answer("📝 Введите новое описание:", reply_markup=back_to_user_menu())
        await state.set_state(SellStates.waiting_for_description)
        return
    if message.text == "✅ ОТПРАВИТЬ":
        data = await state.get_data()
        order = {
            "id": int(datetime.now().timestamp()),
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "product": data['product'],
            "description": data['description'],
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        orders = load_orders_db()
        orders.append(order)
        save_orders(orders)
        
        # Уведомление админам
        from keyboards import order_action_keyboard
        await notify_admins(
            message.bot,
            f"💰 **НОВАЯ ЗАЯВКА НА ПРОДАЖУ!**\n\n"
            f"👤 От: @{message.from_user.username or 'нет'} (ID: {message.from_user.id})\n"
            f"📌 Товар: {data['product']}\n"
            f"📝 Описание: {data['description']}",
            reply_markup=order_action_keyboard(order["id"])
        )
        
        await state.clear()
        await message.answer(
            f"✅ **Заявка отправлена!**\n\n📌 Товар: {data['product']}\nАдминистратор свяжется с вами.",
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
        await message.answer("Главное меню", reply_markup=main_keyboard())
        return
    
    support = {
        "id": int(datetime.now().timestamp()),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "text": message.text,
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    supports = load_supports_db()
    supports.append(support)
    save_supports(supports)
    
    # Уведомление админам
    from keyboards import support_action_keyboard
    await notify_admins(
        message.bot,
        f"🆘 **НОВОЕ ОБРАЩЕНИЕ!**\n\n"
        f"👤 От: @{message.from_user.username or 'нет'} (ID: {message.from_user.id})\n"
        f"📝 Текст: {message.text}",
        reply_markup=support_action_keyboard(support["id"])
    )
    
    await state.clear()
    await message.answer("✅ Обращение отправлено! Администратор ответит вам.", reply_markup=main_keyboard())
