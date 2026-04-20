from aiogram import Router
from user import user_router
from admin import admin_router

callback_router = Router()

# Все callback'и уже обрабатываются в user.py и admin.py
# Этот файл нужен для импорта в bot.py
