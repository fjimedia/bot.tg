import logging
from typing import Any, Dict
from aiogram import Bot

logger = logging.getLogger(__name__)

def validate_input(data: Dict[str, Any]) -> bool:
    """
    Валидация входных данных для объявления
    
    Args:
        data: Словарь с данными объявления
        
    Returns:
        bool: True если данные валидны, False если нет
    """
    try:
        # Проверяем наличие текста и его длину
        text = data.get('text', '')
        if not text or len(text) > 4000:
            logger.warning(f"Invalid text length: {len(text)}")
            return False
            
        # Дополнительные проверки можно добавить здесь
        return True
        
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        return False

async def delete_previous_messages(bot: Bot, chat_id: int, last_message_id: int, count: int = 2) -> None:
    """
    Удаляет предыдущие сообщения в чате
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        last_message_id: ID последнего сообщения
        count: Количество сообщений для удаления (по умолчанию 2)
    """
    for i in range(1, count + 1):
        try:
            await bot.delete_message(chat_id, last_message_id - i)
        except Exception as e:
            logger.warning(f"Failed to delete message {last_message_id - i}: {e}")
            continue