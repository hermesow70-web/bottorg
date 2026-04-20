from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS, MIN_WITHDRAW
from database import *
from keyboards import get_main_menu, get_profile_keyboard
from util import WithdrawStates, ReviewStates, SupportStates

router = Router()

# Проверка бана
async def check_ban(user_id):
    if is_banned(user_id):
        return True
    return False

# === СТАРТ ===
@router.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "нет username"
    add_user(user_id, username)
    
    if not check_consent(user_id):
        text = (
            "🔒 *Данный бот запрашивает соглашение для обработки персональных данных.*\n\n"
            "Мы чтим анонимность, но в данном боте будут обрабатываться платежи.\n\n"
            "1. Вы согласны на обработку персональных данных\n"
            "2. Вы ознакомились с правилами и условиями в этом канале: https://t.me/+ZAJelSN78aliNzIx"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен", callback_data="consent_agree")]
        ])
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await show_welcome(message)

@router.callback_query(F.data == "consent_agree")
async def consent_handler(callback: types.CallbackQuery):
    set_consent(callback.from_user.id)
    
    # Уведомление админам о новом пользователе (только кто нажал согласен)
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(
                admin_id, 
                f"🆕 *Новый пользователь*\n\n👤 Username: @{callback.from_user.username or 'нет username'}\n🆔 ID: `{callback.from_user.id}`\n✅ Согласие получено!"
            )
        except:
            pass
    
    await callback.message.delete()
    await callback.message.answer("✅ Согласие получено!", reply_markup=get_main_menu())
    await callback.answer()

async def show_welcome(event):
    text = "🎉 *Добро пожаловать!*\n\nТут и идут все выплаты, для анонимности и чтобы не путаться)"
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, parse_mode="Markdown", reply_markup=get_main_menu())
        await event.answer()
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=get_main_menu())

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    await show_welcome(callback)

# === ПРОФИЛЬ ===
@router.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    if await check_ban(callback.from_user.id):
        await callback.message.edit_text("❌ Вы забанены! Обратитесь к администратору.")
        await callback.answer()
        return
    
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка", show_alert=True)
        return
    text = f"👤 *Ваш профиль*\n\n📝 Username: @{user[1]}\n💰 Баланс: {user[2]} USDT\n⏳ Заявок в ожидании: {get_pending_withdrawals_count(callback.from_user.id)}"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_profile_keyboard())
    await callback.answer()

# === СПИСОК ЗАЯВОК ===
@router.callback_query(F.data == "my_withdrawals")
async def my_withdrawals(callback: types.CallbackQuery, state: FSMContext):
    if await check_ban(callback.from_user.id):
        await callback.message.edit_text("❌ Вы забанены! Обратитесь к администратору.")
        await callback.answer()
        return
    
    page = (await state.get_data()).get('page', 0)
    withdrawals, total = get_user_withdrawals(callback.from_user.id, page)
    
    if not withdrawals:
        await callback.message.edit_text("📭 У вас пока нет заявок на вывод", reply_markup=get_profile_keyboard())
        await callback.answer()
        return
    
    text = f"📋 *Ваши заявки (всего: {total})*\n\n"
    for w in withdrawals:
        status_emoji = "⏳" if w[3] == "pending" else ("✅" if w[3] == "approved" else "❌")
        status_text = "В ожидании" if w[3] == "pending" else ("Одобрено" if w[3] == "approved" else "Отклонено")
        text += f"{status_emoji} #{w[0]} - {w[1]} USDT ({w[2]})\n   {status_text}\n   📅 {w[4][:16]}\n\n"
    
    keyboard = []
    if total > 8:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data="withdrawals_prev"))
        if (page + 1) * 8 < total:
            nav.append(InlineKeyboardButton(text="Вперед ▶️", callback_data="withdrawals_next"))
        if nav:
            keyboard.append(nav)
    keyboard.append([InlineKeyboardButton(text="🏠 Назад в профиль", callback_data="profile")])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()

@router.callback_query(F.data == "withdrawals_next")
async def withdrawals_next(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 0) + 1
    await state.update_data(page=page)
    await my_withdrawals(callback, state)

@router.callback_query(F.data == "withdrawals_prev")
async def withdrawals_prev(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = max(0, data.get('page', 0) - 1)
    await state.update_data(page=page)
    await my_withdrawals(callback, state)

# === ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (withdraw, review, support) с проверкой бана ===
# Добавьте await check_ban() в начало каждого обработчика
