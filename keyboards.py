from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="📝 Оставить отзыв")],
            [KeyboardButton(text="🆘 Поддержка")],
            [KeyboardButton(text="ℹ️ ИНФО")]
        ],
        resize_keyboard=True
    )

def profile_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Вывести")],
            [KeyboardButton(text="📋 Список заявок")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )

def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Бан/Разбан")],
            [KeyboardButton(text="📋 Заявки")],
            [KeyboardButton(text="💰 Баланс пользователей")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )

def balance_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Начислить")],
            [KeyboardButton(text="➖ Списать")],
            [KeyboardButton(text="🔄 Обнулить")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def ban_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔨 Забанить")],
            [KeyboardButton(text="🔓 Разбанить")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def withdraw_action_keyboard(wid):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{wid}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{wid}")],
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{wid}")]
        ]
    )

def rating_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ 1"), KeyboardButton(text="⭐⭐ 2"), KeyboardButton(text="⭐⭐⭐ 3")],
            [KeyboardButton(text="⭐⭐⭐⭐ 4"), KeyboardButton(text="⭐⭐⭐⭐⭐ 5")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def review_skip_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏩ Пропустить")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
