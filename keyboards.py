from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 ПРОФИЛЬ"), KeyboardButton(text="📝 ОТЗЫВ")],
            [KeyboardButton(text="🆘 ПОДДЕРЖКА"), KeyboardButton(text="ℹ️ ИНФО")]
        ],
        resize_keyboard=True
    )

def profile_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 ВЫВЕСТИ")],
            [KeyboardButton(text="📋 МОИ ЗАЯВКИ")],
            [KeyboardButton(text="◀️ НАЗАД")]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 БАН/РАЗБАН")],
            [KeyboardButton(text="📋 ЗАЯВКИ")],
            [KeyboardButton(text="💰 БАЛАНС")],
            [KeyboardButton(text="◀️ НАЗАД")]
        ],
        resize_keyboard=True
    )

def balance_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ НАЧИСЛИТЬ"), KeyboardButton(text="➖ СПИСАТЬ")],
            [KeyboardButton(text="🔄 ОБНУЛИТЬ")],
            [KeyboardButton(text="◀️ НАЗАД")]
        ],
        resize_keyboard=True
    )

def ban_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔨 ЗАБАНИТЬ"), KeyboardButton(text="🔓 РАЗБАНИТЬ")],
            [KeyboardButton(text="◀️ НАЗАД")]
        ],
        resize_keyboard=True
    )

def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ НАЗАД")]],
        resize_keyboard=True
    )

def withdraw_amount_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ НАЗАД")]],
        resize_keyboard=True
    )

def withdraw_method_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 КАРТА")],
            [KeyboardButton(text="🤖 CRYPTO BOT")],
            [KeyboardButton(text="◀️ НАЗАД")]
        ],
        resize_keyboard=True
    )

def withdraw_card_type_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 СБП")],
            [KeyboardButton(text="💳 НОМЕР КАРТЫ")],
            [KeyboardButton(text="◀️ НАЗАД")]
        ],
        resize_keyboard=True
    )

def rating_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ 1"), KeyboardButton(text="⭐⭐ 2"), KeyboardButton(text="⭐⭐⭐ 3")],
            [KeyboardButton(text="⭐⭐⭐⭐ 4"), KeyboardButton(text="⭐⭐⭐⭐⭐ 5")],
            [KeyboardButton(text="◀️ НАЗАД")]
        ],
        resize_keyboard=True
    )

def review_skip_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏩ ПРОПУСТИТЬ")],
            [KeyboardButton(text="◀️ НАЗАД")]
        ],
        resize_keyboard=True
    )

def support_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ НАЗАД")]],
        resize_keyboard=True
    )

def withdraw_action_keyboard(wid):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ ОДОБРИТЬ", callback_data=f"approve_{wid}")],
            [InlineKeyboardButton(text="❌ ОТКЛОНИТЬ", callback_data=f"reject_{wid}")],
            [InlineKeyboardButton(text="💬 ОТВЕТИТЬ", callback_data=f"reply_{wid}")]
        ]
            )
