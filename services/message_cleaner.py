from aiogram import Bot
from typing import Dict, List

class MessageCleaner:
    def __init__(self):
        self.user_messages: Dict[int, List[int]] = {}
        self.bot_messages: Dict[int, List[int]] = {}

    async def add_message(self, chat_id: int, message_id: int, is_bot: bool = False):
        target = self.bot_messages if is_bot else self.user_messages
        if chat_id not in target:
            target[chat_id] = []
        target[chat_id].append(message_id)

    async def clean_chat(self, bot: Bot, chat_id: int):
        for messages in [self.user_messages, self.bot_messages]:
            if chat_id in messages:
                for msg_id in messages[chat_id]:
                    try:
                        await bot.delete_message(chat_id, msg_id)
                    except Exception:
                        pass
                messages[chat_id] = []