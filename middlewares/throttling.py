import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware

logger = logging.getLogger(__name__)

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate: int = 5, per: float = 10.0):
        self.rate = rate
        self.per = timedelta(seconds=per)
        self.user_timestamps = defaultdict(list)
        super().__init__()

    async def __call__(self, handler, event: types.Message, data):
        user_id = event.from_user.id
        now = datetime.now()

        # Очищаем старые запросы
        self.user_timestamps[user_id] = [
            t for t in self.user_timestamps[user_id] 
            if now - t < self.per
        ]

        # Проверяем лимит
        if len(self.user_timestamps[user_id]) >= self.rate:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            await event.answer("⚠️ Слишком много запросов! Пожалуйста, подождите.")
            return

        # Добавляем текущий запрос
        self.user_timestamps[user_id].append(now)
        return await handler(event, data)

def setup_throttling(dp):
    dp.message.middleware(ThrottlingMiddleware(rate=5, per=10))  # 5 сообщений в 10 секунд