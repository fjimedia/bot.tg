from aiogram import Bot
from aiogram.exceptions import TelegramConflictError
import logging
import asyncio

logger = logging.getLogger(__name__)

async def handle_conflict_error(bot: Bot, retry_count: int = 3):
    for attempt in range(retry_count):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Successfully resolved conflict")
            return True
        except TelegramConflictError:
            wait_time = (attempt + 1) * 5  # Экспоненциальная задержка
            logger.warning(f"Conflict detected, attempt {attempt + 1}. Waiting {wait_time} sec...")
            await asyncio.sleep(wait_time)
    return False