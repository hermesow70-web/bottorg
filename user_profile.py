from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import get_user, get_active_requests_count
from keyboards import main_menu, profile_menu, back_menu
from utils import notify_admins

profile_router = Router()

@profile_router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("❌ Ошибка", reply_markup=main_menu())
        await callback.answer()
        return
    
    active_count = get_active_requests_count(callback.from_user.id)
    text = (
        f"👤 **Ваш профиль**\n\n"
        f"💰 **Баланс:** {user['balance']} USDT\n"
        f"📋 **Активных заявок:** {active_count}\n"
        f"📤 **Выведено всего:** {user['total_withdrawn']} USDT"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=profile_menu())
    await callback.answer()

@profile_router.callback_query(F.data == "my_requests")
async def my_requests_callback(callback: CallbackQuery):
    from database import get_user_withdraws
    withdraws = get_user_withdraws(callback.from_user.id)
    if not withdraws:
        await callback.answer("У вас нет заявок", show_alert=True)
        return
    
    withdraws.reverse()
    text = "📋 **Ваши заявки на вывод:**\n\n"
    status_map = {"pending": "⏳ В ожидании", "approved": "✅ Одобрено", "rejected": "❌ Отклонено"}
    
    for w in withdraws[:10]:
        text += f"• {w['amount']} USDT - {status_map.get(w['status'], '⏳ В ожидании')} - {w['created_at'][:10]}\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=profile_menu())
    await callback.answer()

@profile_router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔥 **Добро пожаловать!**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await callback.answer()
