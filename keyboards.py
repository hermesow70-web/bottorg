from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="review")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ])

def get_profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Вывести", callback_data="withdraw")],
        [InlineKeyboardButton(text="📋 Список заявок", callback_data="my_withdrawals")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_rating_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 1", callback_data="rating_1"),
         InlineKeyboardButton(text="⭐⭐ 2", callback_data="rating_2"),
         InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data="rating_3"),
         InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data="rating_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data="rating_5")]
    ])
