from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📝 Отзыв")],
            [KeyboardButton(text="🆘 Поддержка"), KeyboardButton(text="ℹ️ Инфо")]
        ],
        resize_keyboard=True
    )

def profile_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Вывести")],
            [KeyboardButton(text="📋 Мои заявки")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Бан/Разбан")],
            [KeyboardButton(text="📋 Заявки")],
            [KeyboardButton(text="💰 Баланс")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def balance_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Начислить")],
            [KeyboardButton(text="➖ Списать")],
            [KeyboardButton(text="🔄 Обнулить")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def ban_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔨 Забанить")],
            [KeyboardButton(text="🔓 Разбанить")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ Назад")]],
        resize_keyboard=True
    )

def withdraw_amount_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ Назад")]],
        resize_keyboard=True
    )

def withdraw_method_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Карта")],
            [KeyboardButton(text="🤖 Crypto Bot")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def withdraw_card_type_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 СБП")],
            [KeyboardButton(text="💳 Номер карты")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def rating_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ 1"), KeyboardButton(text="⭐⭐ 2"), KeyboardButton(text="⭐⭐⭐ 3")],
            [KeyboardButton(text="⭐⭐⭐⭐ 4"), KeyboardButton(text="⭐⭐⭐⭐⭐ 5")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def review_skip_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏩ Пропустить")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )

def review_anonymous_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Отправить с именем", callback_data="review_named")],
            [InlineKeyboardButton(text="👤 Отправить анонимно", callback_data="review_anonymous")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="review_cancel")]
        ]
    )

def withdraw_action_keyboard(wid):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{wid}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{wid}")],
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{wid}")]
        ]
            )
