from config import ADMIN_IDS

async def notify_admins(bot, text, reply_markup=None):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown", reply_markup=reply_markup)
        except:
            pass

async def notify_user(bot, user_id, text):
    try:
        await bot.send_message(user_id, text, parse_mode="Markdown")
    except:
        pass
