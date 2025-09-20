from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import logging
from config.states import States
from config import settings, messages
from config.keyboard_layouts import get_main_menu, generate_channels_kb, generate_durations_kb
from config.states import States
from database.crud import get_or_create_user
from database.session import get_db
from services.message_cleaner import MessageCleaner
import asyncio

logger = logging.getLogger(__name__)
user_router = Router(name='user_router')

# Главное меню
@user_router.message(Command("start"))
async def cmd_start(message: types.Message, cleaner: MessageCleaner):
    """Обработчик команды /start"""
    try:
        await cleaner.clean_chat(message.bot, message.chat.id)
        
        # Регистрация/получение пользователя
        db = next(get_db())
        user = get_or_create_user(
            db,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )
        
        logger.info(f"User {message.from_user.id} started the bot")
        
        await message.answer(
            messages.START,
            reply_markup=get_main_menu(message.from_user.id in settings.ADMIN_IDS)
        )
    except Exception as e:
        logger.error(f"Start command error: {e}")
        await message.answer("⚠️ Произошла ошибка, попробуйте позже")

# Навигация
@user_router.message(F.text == "◀️ На главную")
@user_router.message(F.text == "🔙 Назад")
async def back_to_main(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Возврат в главное меню"""
    await state.clear()
    await cmd_start(message, cleaner)

# Баланс и платежи
@user_router.message(F.text == "💰 Баланс")
@user_router.message(Command("payment"))
async def handle_payment(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Управление балансом"""
    await cleaner.clean_chat(message.bot, message.chat.id)
    await state.clear()
    
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="💳 Пополнить баланс"))
    builder.row(types.KeyboardButton(text="📊 История платежей"))
    builder.row(types.KeyboardButton(text="◀️ На главную"))
    
    await message.answer(
        "💰 <b>Ваш баланс:</b> 0 руб\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@user_router.message(F.text == "💳 Пополнить баланс")
async def process_payment(message: types.Message, cleaner: MessageCleaner):
    """Пополнение баланса"""
    await cleaner.clean_chat(message.bot, message.chat.id)
    
    builder = ReplyKeyboardBuilder()
    amounts = ["100 руб", "300 руб", "500 руб", "1000 руб"]
    for amount in amounts:
        builder.add(types.KeyboardButton(text=amount))
    builder.adjust(2)
    builder.row(types.KeyboardButton(text="◀️ Назад"))
    
    await message.answer(
        "💳 <b>Пополнение баланса</b>\n\n"
        "Выберите сумму:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

# Размещение рекламы
@user_router.message(F.text == "📢 Разместить рекламу")
async def start_ad(message: types.Message, state: FSMContext, bot: Bot, cleaner: MessageCleaner):
    """Начало процесса размещения рекламы"""
    try:
        await cleaner.clean_chat(bot, message.chat.id)
        
        # Показываем сообщение загрузки
        load_msg = await message.answer("⏳ Загрузка доступных каналов...")
        await asyncio.sleep(1)  # Имитация загрузки
        await bot.delete_message(message.chat.id, load_msg.message_id)
        
        # Предлагаем выбрать канал
        await message.answer(
            messages.CHANNEL_CHOICE,
            reply_markup=generate_channels_kb()
        )
        await state.set_state(States.select_channel)
        
        logger.info(f"User {message.from_user.id} started ad placement")
    except Exception as e:
        logger.error(f"Ad start error: {e}")
        await message.answer("⚠️ Ошибка при запуске размещения")

@user_router.message(States.select_channel, F.text.in_(settings.CHANNELS.keys()))
async def select_channel(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Выбор канала для рекламы"""
    try:
        await cleaner.clean_chat(message.bot, message.chat.id)
        await state.update_data(channel=message.text)
        
        await message.answer(
            f"Выбран канал: <b>{message.text}</b>\n"
            "Теперь выберите срок размещения:",
            reply_markup=generate_durations_kb()
        )
        await state.set_state(States.select_duration)
    except Exception as e:
        logger.error(f"Channel select error: {e}")
        await message.answer("⚠️ Ошибка при выборе канала")

@user_router.message(States.select_channel)
async def invalid_channel(message: types.Message):
    """Некорректный выбор канала"""
    await message.answer(
        "❌ Пожалуйста, выберите канал из списка ниже:",
        reply_markup=generate_channels_kb()
    )

@user_router.message(States.select_duration, F.text.in_(settings.PRICES))
async def select_duration(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Выбор длительности размещения"""
    try:
        data = await state.get_data()
        price_info = settings.PRICES[message.text]
        
        await cleaner.clean_chat(message.bot, message.chat.id)
        
        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="Пропустить"))
        builder.row(types.KeyboardButton(text="◀️ Назад"))
        
        await message.answer(
            f"📌 <b>Вы выбрали:</b>\n"
            f"Канал: {data['channel']}\n"
            f"Срок: {message.text}\n"
            f"Цена: {price_info['price']} руб.\n\n"
            "Отправьте фото/видео для объявления (или нажмите 'Пропустить'):",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
        await state.update_data(
            duration=message.text, 
            price=price_info['price'],
            currency=price_info.get('currency', 'RUB')
        )
        await state.set_state(States.enter_media)
    except Exception as e:
        logger.error(f"Duration select error: {e}")
        await message.answer("⚠️ Ошибка при выборе срока")

# Медиа в объявлениях
@user_router.message(States.enter_media, F.content_type.in_({'photo', 'video'}))
async def handle_ad_media(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Обработка медиа для объявления"""
    try:
        media_type = 'photo' if message.photo else 'video'
        media_id = message.photo[-1].file_id if message.photo else message.video.file_id
        
        await state.update_data(media_type=media_type, media_id=media_id)
        await cleaner.clean_chat(message.bot, message.chat.id)
        
        await message.answer(
            "🖼️ Медиа-контент сохранён!\n\n"
            "Теперь введите текст объявления (максимум 500 символов):",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(States.enter_text)
    except Exception as e:
        logger.error(f"Media upload error: {e}")
        await message.answer("⚠️ Ошибка при загрузке медиа")

@user_router.message(States.enter_media, F.text == "Пропустить")
async def skip_media(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Пропуск добавления медиа"""
    await cleaner.clean_chat(message.bot, message.chat.id)
    await message.answer(
        "Введите текст объявления (максимум 500 символов):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(States.enter_text)

# Текст объявления
@user_router.message(States.enter_text)
async def process_ad_text(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Обработка текста объявления"""
    try:
        if len(message.text) > 500:
            return await message.answer("❌ Превышен лимит в 500 символов")
        
        data = await state.get_data()
        await cleaner.clean_chat(message.bot, message.chat.id)
        
        # Формируем текст подтверждения
        confirmation_text = (
            "✅ <b>Объявление успешно создано!</b>\n\n"
            f"📢 Канал: {data['channel']}\n"
            f"⏳ Срок: {data['duration']}\n"
            f"💰 Стоимость: {data['price']} {data['currency']}\n\n"
            f"📝 Текст объявления:\n{message.text}\n\n"
            "Ожидайте подтверждения модератора."
        )
        
        # Отправляем объявление
        if 'media_id' in data:
            if data['media_type'] == 'photo':
                await message.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=data['media_id'],
                    caption=confirmation_text
                )
            else:
                await message.bot.send_video(
                    chat_id=message.chat.id,
                    video=data['media_id'],
                    caption=confirmation_text
                )
        else:
            await message.answer(confirmation_text)
        
        await state.clear()
        await cmd_start(message, cleaner)
        
        logger.info(f"New ad created by {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ad creation error: {e}")
        await message.answer("⚠️ Ошибка при создании объявления")

# Отмена действий
@user_router.message(F.text == "❌ Отмена")
async def cancel_ad(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Отмена текущего действия"""
    await state.clear()
    await cleaner.clean_chat(message.bot, message.chat.id)
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=get_main_menu(message.from_user.id in settings.ADMIN_IDS)
    )