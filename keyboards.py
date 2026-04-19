from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    kb = [
        [KeyboardButton(text="👤 ПРОФИЛЬ")],
        [KeyboardButton(text="📜 ИСТОРИЯ ВЫВОДОВ")],
        [KeyboardButton(text="⭐ ОСТАВИТЬ ОТЗЫВ")],
        [KeyboardButton(text="💰 ВЫВОД СРЕДСТВ")],
        [KeyboardButton(text="ℹ️ ИНФО")],
        [KeyboardButton(text="🆘 ПОДДЕРЖКА")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def profile_keyboard():
    kb = [
        [KeyboardButton(text="💰 ВЫВОД СРЕДСТВ")],
        [KeyboardButton(text="📜 ИСТОРИЯ ВЫВОДОВ")],
        [KeyboardButton(text="🔙 Назад в главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def back_keyboard():
    kb = [[KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def main_menu_keyboard():
    kb = [[KeyboardButton(text="🏠 Главное меню")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def cancel_keyboard():
    kb = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_keyboard():
    kb = [
        [KeyboardButton(text="➕ ЗАЧИСЛИТЬ БАЛАНС")],
        [KeyboardButton(text="➖ СПИСАТЬ БАЛАНС")],
        [KeyboardButton(text="🔧 ИЗМЕНИТЬ БАЛАНС")],
        [KeyboardButton(text="✅ ЗАЯВКИ НА ВЫВОД")],
        [KeyboardButton(text="⭐ УПРАВЛЕНИЕ РЕЙТИНГОМ")],
        [KeyboardButton(text="📋 СПИСОК ОТЗЫВОВ")],
        [KeyboardButton(text="📢 РАССЫЛКА")],
        [KeyboardButton(text="👥 БАН/РАЗБАН")],
        [KeyboardButton(text="📊 ПРОСМОТР ПОЛЬЗОВАТЕЛЯ")],
        [KeyboardButton(text="🔙 ВЫЙТИ ИЗ АДМИНКИ")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def rating_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 1", callback_data="rating_1"),
         InlineKeyboardButton(text="⭐⭐ 2", callback_data="rating_2"),
         InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data="rating_3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data="rating_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data="rating_5")]
    ])

def anonymous_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Отправить с моим именем", callback_data="review_named")],
        [InlineKeyboardButton(text="👤 Отправить анонимно", callback_data="review_anonymous")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="review_cancel")]
    ])

def skip_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Написать", callback_data="review_write")],
        [InlineKeyboardButton(text="⏩ Пропустить", callback_data="review_skip")]
    ])

def withdraw_method_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Банковская карта", callback_data="withdraw_card")],
        [InlineKeyboardButton(text="₿ Криптокошелёк (ссылка)", callback_data="withdraw_crypto")],
        [InlineKeyboardButton(text="📞 Связаться с админом", callback_data="withdraw_contact")]
    ])

def pagination_keyboard(page, total_pages, prefix):
    kb = []
    row = []
    if page > 1:
        row.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"{prefix}_page_{page-1}"))
    row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        row.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"{prefix}_page_{page+1}"))
    kb.append(row)
    kb.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
