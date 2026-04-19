from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    kb = [
        [KeyboardButton(text="ℹ️ ИНФО")],
        [KeyboardButton(text="📌 АКТУАЛ")],
        [KeyboardButton(text="💰 ПРОДАТЬ")],
        [KeyboardButton(text="🆘 ПОДДЕРЖКА")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_main_keyboard():
    kb = [
        [KeyboardButton(text="👥 БАН/РАЗБАН")],
        [KeyboardButton(text="📋 СПИСОК ЖАЛОБ")],
        [KeyboardButton(text="📦 СПИСОК ЗАЯВОК")],
        [KeyboardButton(text="📌 УПРАВЛЕНИЕ АКТУАЛ")],
        [KeyboardButton(text="📢 РАССЫЛКА")],
        [KeyboardButton(text="👤 СПИСОК ПОЛЬЗОВАТЕЛЕЙ")],
        [KeyboardButton(text="📊 СТАТИСТИКА")],
        [KeyboardButton(text="🔍 ПОИСК")],
        [KeyboardButton(text="🔙 ВЫЙТИ ИЗ АДМИНКИ")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def back_to_user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад в главное меню")]],
        resize_keyboard=True
    )

def back_to_admin():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад в админку")]],
        resize_keyboard=True
    )

def order_action_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_order_{order_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_order_{order_id}")],
        [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_order_{order_id}")]
    ])

def support_action_keyboard(support_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_support_{support_id}")],
        [InlineKeyboardButton(text="🗑 Отклонить", callback_data=f"delete_support_{support_id}")]
    ])

def search_keyboard():
    kb = [
        [KeyboardButton(text="🔍 Поиск по ID")],
        [KeyboardButton(text="🔍 Поиск по username")],
        [KeyboardButton(text="🔙 Назад в админку")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
