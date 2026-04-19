from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 ПРОФИЛЬ")],
            [KeyboardButton(text="📜 ИСТОРИЯ ВЫВОДОВ")],
            [KeyboardButton(text="⭐ ОСТАВИТЬ ОТЗЫВ")],
            [KeyboardButton(text="💰 ВЫВОД СРЕДСТВ")],
            [KeyboardButton(text="ℹ️ ИНФО")],
            [KeyboardButton(text="🆘 ПОДДЕРЖКА")]
        ],
        resize_keyboard=True
    )

def profile_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 ВЫВОД СРЕДСТВ")],
            [KeyboardButton(text="📜 ИСТОРИЯ ВЫВОДОВ")],
            [KeyboardButton(text="🔙 НАЗАД")]
        ],
        resize_keyboard=True
    )

def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 НАЗАД")]],
        resize_keyboard=True
    )

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ ОТМЕНА")]],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ ЗАЧИСЛИТЬ БАЛАНС")],
            [KeyboardButton(text="➖ СПИСАТЬ БАЛАНС")],
            [KeyboardButton(text="🔧 ИЗМЕНИТЬ БАЛАНС")],
            [KeyboardButton(text="✅ ЗАЯВКИ НА ВЫВОД")],
            [KeyboardButton(text="⭐ УПРАВЛЕНИЕ РЕЙТИНГОМ")],
            [KeyboardButton(text="📋 СПИСОК ОТЗЫВОВ")],
            [KeyboardButton(text="📢 РАССЫЛКА")],
            [KeyboardButton(text="👥 БАН/РАЗБАН")],
            [KeyboardButton(text="📊 ПРОСМОТР ПОЛЬЗОВАТЕЛЯ")],
            [KeyboardButton(text="🔙 ВЫЙТИ")]
        ],
        resize_keyboard=True
    )

def rating_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ 1", callback_data="rating_1"), InlineKeyboardButton(text="⭐⭐ 2", callback_data="rating_2"), InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data="rating_3")],
            [InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data="rating_4"), InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data="rating_5")]
        ]
    )

def review_actions_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 НАПИСАТЬ", callback_data="review_write"), InlineKeyboardButton(text="⏩ ПРОПУСТИТЬ", callback_data="review_skip")]
        ]
    )

def anonymous_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 С ИМЕНЕМ", callback_data="review_named"), InlineKeyboardButton(text="👤 АНОНИМНО", callback_data="review_anonymous")],
            [InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="review_cancel")]
        ]
    )

def withdraw_method_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 БАНКОВСКАЯ КАРТА", callback_data="withdraw_card")],
            [InlineKeyboardButton(text="₿ КРИПТОКОШЕЛЁК (ССЫЛКА)", callback_data="withdraw_crypto")],
            [InlineKeyboardButton(text="📞 СВЯЗАТЬСЯ С АДМИНОМ", callback_data="withdraw_contact")]
        ]
    )

def withdraw_action_keyboard(wid):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ ОДОБРИТЬ", callback_data=f"approve_{wid}")],
            [InlineKeyboardButton(text="❌ ОТКЛОНИТЬ", callback_data=f"reject_{wid}")]
        ]
    )

def pagination_keyboard(page, total, prefix):
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="◀️ НАЗАД", callback_data=f"{prefix}_{page-1}"))
    buttons.append(InlineKeyboardButton(text=f"{page}/{total}", callback_data="ignore"))
    if page < total:
        buttons.append(InlineKeyboardButton(text="ВПЕРЁД ▶️", callback_data=f"{prefix}_{page+1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="to_main")]])
