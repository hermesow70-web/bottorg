from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📝 Отзыв", callback_data="review")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")]
    ])

def profile_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Вывести", callback_data="withdraw_start")],
        [InlineKeyboardButton(text="📋 Мои заявки", callback_data="my_requests")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])

def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Бан/Разбан", callback_data="admin_ban")],
        [InlineKeyboardButton(text="📋 Заявки", callback_data="admin_requests")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="admin_balance")],
        [InlineKeyboardButton(text="◀️ Выход", callback_data="back_to_main")]
    ])

def admin_ban_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔨 Забанить", callback_data="ban_user")],
        [InlineKeyboardButton(text="🔓 Разбанить", callback_data="unban_user")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])

def admin_balance_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Начислить", callback_data="balance_add")],
        [InlineKeyboardButton(text="➖ Списать", callback_data="balance_subtract")],
        [InlineKeyboardButton(text="🔄 Обнулить", callback_data="balance_reset")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])

def rating_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 1", callback_data="rate_1"),
         InlineKeyboardButton(text="⭐⭐ 2", callback_data="rate_2"),
         InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data="rate_3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data="rate_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data="rate_5")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])

def review_options_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Написать", callback_data="review_write")],
        [InlineKeyboardButton(text="⏩ Пропустить", callback_data="review_skip")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="review")]
    ])

def anonymous_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Отправить с именем", callback_data="review_named")],
        [InlineKeyboardButton(text="👤 Отправить анонимно", callback_data="review_anonymous")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="review_cancel")]
    ])

def withdraw_method_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Карта", callback_data="method_card")],
        [InlineKeyboardButton(text="🤖 Crypto Bot", callback_data="method_crypto")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
    ])

def withdraw_card_type_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 СБП", callback_data="card_sbp")],
        [InlineKeyboardButton(text="💳 Номер карты", callback_data="card_number")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="withdraw_start")]
    ])

def withdraw_action_menu(wid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{wid}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{wid}")],
        [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{wid}")]
    ])
