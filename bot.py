import asyncio
import logging
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config.settings import settings
from database.session import init_db, engine
from services.lock_system import InstanceLock
from typing import Dict, Any, List, Tuple, Optional

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,  # <- ИЗМЕНИТЕ с INFO на DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot_errors.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Form(StatesGroup):
    select_channel = State()
    select_duration = State()
    enter_media = State()
    enter_text = State()

class MessageCleaner:
    def __init__(self):
        self.user_messages = {}
        self.bot_messages = {}

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

async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    try:
        await bot.send_message(
            settings.ADMIN_IDS[0], 
            "🟢 Бот успешно запущен\n"
            f"Версия: 2.1\n"
            f"Админов: {len(settings.ADMIN_IDS)}"
        )
        init_db()
    except Exception as e:
        logger.error(f"Startup error: {e}")

async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    try:
        await engine.dispose()
        await bot.send_message(settings.ADMIN_IDS[0], "🔴 Бот остановлен")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    finally:
        await bot.session.close()

async def show_loading(bot: Bot, chat_id: int, text: str = "⏳ Загрузка...") -> int:
    """Показывает сообщение загрузки и возвращает его ID"""
    msg = await bot.send_message(chat_id, text)
    return msg.message_id

async def setup_routers(dp: Dispatcher, bot: Bot, cleaner: MessageCleaner, show_loading_func):
    """Настройка всех роутеров и обработчиков"""
    
    # Главное меню
    @dp.message(Command("start", "help"))
    async def cmd_start(message: types.Message, state: FSMContext):
        try:
            await state.clear()
            await cleaner.clean_chat(bot, message.chat.id)
            
            builder = ReplyKeyboardBuilder()
            buttons = [
                "📢 Разместить рекламу",
                "📋 Мои объявления",
                "💰 Баланс",
                "🆘 Помощь",
                "◀️ На главную"
            ]
            
            for button in buttons[:-1]:
                builder.add(types.KeyboardButton(text=button))
            builder.adjust(2, 2, 1)
            
            if message.from_user.id in settings.ADMIN_IDS:
                builder.row(types.KeyboardButton(text="👑 Админ-панель"))
            
            msg = await message.answer(
                "🔹 Добро пожаловать! Выберите действие:",
                reply_markup=builder.as_markup(resize_keyboard=True)
            )
            await cleaner.add_message(message.chat.id, msg.message_id)
        except Exception as e:
            logger.error(f"Start command error: {e}")
            await message.answer("⚠️ Ошибка, попробуйте позже")

    # Обработка кнопки "На главную"
    @dp.message(F.text == "◀️ На главную")
    async def back_to_main(message: types.Message, state: FSMContext):
        await cmd_start(message, state)

    # Обработка кнопки "Разместить рекламу"
    @dp.message(F.text == "📢 Разместить рекламу")
    async def start_advert(message: types.Message, state: FSMContext):
        try:
            await cleaner.clean_chat(bot, message.chat.id)
            load_msg_id = await show_loading_func(bot, message.chat.id)
            
            builder = ReplyKeyboardBuilder()
            for channel in settings.CHANNELS:
                builder.add(types.KeyboardButton(text=channel))
            builder.adjust(2)
            builder.row(types.KeyboardButton(text="◀️ На главную"))
            
            await bot.delete_message(message.chat.id, load_msg_id)
            msg = await message.answer(
                "📢 Выберите канал для рекламы:",
                reply_markup=builder.as_markup(resize_keyboard=True)
            )
            await cleaner.add_message(message.chat.id, msg.message_id)
            await state.set_state(Form.select_channel)
        except Exception as e:
            logger.error(f"Advert start error: {e}")
            await message.answer("⚠️ Ошибка при запуске размещения")

    # Обработка выбора канала
    @dp.message(Form.select_channel, F.text.in_(settings.CHANNELS))
    async def select_channel(message: types.Message, state: FSMContext):
        try:
            await cleaner.clean_chat(bot, message.chat.id)
            load_msg_id = await show_loading(bot, message.chat.id)
            
            builder = ReplyKeyboardBuilder()
            for duration, price in settings.PRICES.items():
                builder.add(types.KeyboardButton(
                    text=f"{duration} - {price['amount']} руб"
                ))
            builder.adjust(2)
            builder.row(types.KeyboardButton(text="◀️ Назад"))
            
            await bot.delete_message(message.chat.id, load_msg_id)
            msg = await message.answer(
                f"Выбран канал: {message.text}\n"
                "📅 Выберите срок размещения:",
                reply_markup=builder.as_markup(resize_keyboard=True)
            )
            await cleaner.add_message(message.chat.id, msg.message_id)
            await state.update_data(channel=message.text)
            await state.set_state(Form.select_duration)
        except Exception as e:
            logger.error(f"Channel select error: {e}")
            await message.answer("⚠️ Ошибка при выборе канала")

    # Обработка кнопки "Назад" при выборе канала
    @dp.message(Form.select_channel, F.text == "◀️ Назад")
    async def back_from_channels(message: types.Message, state: FSMContext):
    # Очищаем состояние и возвращаемся в главное меню
               await state.clear()
               await cmd_start(message, state)

    # Обработка выбора срока
    @dp.message(Form.select_duration)
    async def select_duration(message: types.Message, state: FSMContext):
        try:
            selected_text = message.text.split(' - ')[0]
            
            if selected_text in settings.PRICES:
                await cleaner.clean_chat(bot, message.chat.id)
                price = settings.PRICES[selected_text]
                await state.update_data(
                    duration=selected_text,
                    price=price['amount']
                )
                
                builder = ReplyKeyboardBuilder()
                builder.add(types.KeyboardButton(text="Пропустить"))
                builder.row(types.KeyboardButton(text="◀️ Назад"))
                
                msg = await message.answer(
                    f"📌 Вы выбрали:\n"
                    f"Канал: {(await state.get_data())['channel']}\n"
                    f"Срок: {selected_text}\n"
                    f"Цена: {price['amount']} руб\n\n"
                    "Отправьте фото или видео для объявления (или нажмите 'Пропустить'):",
                    reply_markup=builder.as_markup(resize_keyboard=True)
                )
                await cleaner.add_message(message.chat.id, msg.message_id)
                await state.set_state(Form.enter_media)
            else:
                await message.answer("Пожалуйста, выберите срок из предложенных вариантов")
        except Exception as e:
            logger.error(f"Duration select error: {e}")
            await message.answer("⚠️ Ошибка при выборе срока")

    # Обработка медиа-контента
    @dp.message(Form.enter_media, F.content_type.in_({'photo', 'video'}))
    async def handle_media(message: types.Message, state: FSMContext):
        try:
            if message.photo:
                media_id = message.photo[-1].file_id
                media_type = "photo"
            elif message.video:
                media_id = message.video.file_id
                media_type = "video"
            
            await state.update_data(media_id=media_id, media_type=media_type)
            await cleaner.clean_chat(bot, message.chat.id)
            
            msg = await message.answer(
                "Медиа-контент сохранён. Теперь введите текст объявления (максимум 1000 символов):",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await cleaner.add_message(message.chat.id, msg.message_id)
            await state.set_state(Form.enter_text)
        except Exception as e:
            logger.error(f"Media handling error: {e}")
            await message.answer("⚠️ Ошибка при обработке медиа")

    # Пропуск добавления медиа
    @dp.message(Form.enter_media, F.text == "Пропустить")
    async def skip_media(message: types.Message, state: FSMContext):
        await cleaner.clean_chat(bot, message.chat.id)
        msg = await message.answer(
            "Введите текст объявления (максимум 1000 символов):",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await cleaner.add_message(message.chat.id, msg.message_id)
        await state.set_state(Form.enter_text)

    # Назад к выбору срока
    @dp.message(Form.enter_media, F.text == "◀️ Назад")
    async def back_from_media(message: types.Message, state: FSMContext):
        data = await state.get_data()
        await cleaner.clean_chat(bot, message.chat.id)
        
        builder = ReplyKeyboardBuilder()
        for duration, price in settings.PRICES.items():
            builder.add(types.KeyboardButton(
                text=f"{duration} - {price['amount']} руб"
            ))
        builder.adjust(2)
        builder.row(types.KeyboardButton(text="◀️ Назад"))
        
        msg = await message.answer(
            f"Выбран канал: {data['channel']}\n"
            "📅 Выберите срок размещения:",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
        await cleaner.add_message(message.chat.id, msg.message_id)
        await state.set_state(Form.select_duration)

    # Обработка ввода текста объявления
    @dp.message(Form.enter_text)
    async def enter_ad_text(message: types.Message, state: FSMContext):
        try:
            if len(message.text) > 1000:
                await message.answer("Текст слишком длинный (максимум 1000 символов)")
                return
            
            data = await state.get_data()
            await cleaner.clean_chat(bot, message.chat.id)
            
            # Формируем текст объявления
            ad_text = (
                f"✅ Объявление успешно создано!\n"
                f"Канал: {data['channel']}\n"
                f"Срок: {data['duration']}\n"
                f"Цена: {data['price']} руб\n\n"
                f"Текст объявления:\n{message.text}\n\n"
                "Ожидайте подтверждения администратора."
            )
            
            # Если есть медиа - отправляем его с текстом
            if 'media_id' in data:
                if data['media_type'] == 'photo':
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=data['media_id'],
                        caption=ad_text
                    )
                elif data['media_type'] == 'video':
                    await bot.send_video(
                        chat_id=message.chat.id,
                        video=data['media_id'],
                        caption=ad_text
                    )
            else:
                # Только текст
                await message.answer(ad_text)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Ad text error: {e}")
            await message.answer("⚠️ Ошибка при создании объявления")

    # Обработка кнопок меню
    @dp.message(F.text.in_(["📋 Мои объявления", "💰 Баланс", "🆘 Помощь"]))
    async def handle_menu_buttons(message: types.Message):
        try:
            await cleaner.clean_chat(bot, message.chat.id)
            if message.text == "📋 Мои объявления":
                response = "📋 Ваши объявления:\n(здесь будет список ваших объявлений)"
            elif message.text == "💰 Баланс":
                response = "💰 Ваш баланс: 0 руб\nПополнить баланс: /payment"
            elif message.text == "🆘 Помощь":
                response = ("🆘 Помощь:\n"
                          "/start - Главное меню\n"
                          "/help - Эта справка\n"
                          "По вопросам: @support")
            
            msg = await message.answer(response)
            await cleaner.add_message(message.chat.id, msg.message_id)
        except Exception as e:
            logger.error(f"Menu button error: {e}")
            await message.answer("⚠️ Ошибка при обработке запроса")

async def main():
    """Основная функция бота"""
    lock = InstanceLock()
    if not lock.acquire():
        logger.critical("Another instance is already running. Exiting.")
        return

    try:
        # Инициализация бота и диспетчера
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode="HTML")
        )
        dp = Dispatcher(storage=MemoryStorage())
        cleaner = MessageCleaner()

        # Настройка роутеров
        await setup_routers(dp, bot, cleaner, show_loading)

        # Подключение обработчиков startup/shutdown
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Запуск бота
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
    finally:
        lock.release()
        if 'bot' in locals():
            await bot.session.close()

if __name__ == "__main__":
    if not Path(".env").exists():
        print("ОШИБКА: Создайте файл .env с токеном!")
        sys.exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")