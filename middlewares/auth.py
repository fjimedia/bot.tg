from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from config.settings import settings

class AdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data):
        if any(
            cmd in event.text for cmd in ["/admin", "👑 Админ"]
        ) and event.from_user.id not in settings.ADMIN_IDS:
            await event.answer("⛔ У вас нет прав доступа!")
            return
        return await handler(event, data)