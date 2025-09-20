from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardRemove

from services.message_cleaner import MessageCleaner
from config import settings
from database.session import get_db
from database.models import User, Ad
from sqlalchemy import select, func
from datetime import datetime, timedelta
import logging
import asyncio

admin_router = Router(name='admin_router')
logger = logging.getLogger(__name__)

async def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in settings.ADMIN_IDS

def get_admin_keyboard():
    """Клавиатура админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📈 Статистика"))
    builder.row(types.KeyboardButton(text="📢 Рассылка"))
    builder.row(types.KeyboardButton(text="✅ Модерация"))
    builder.row(types.KeyboardButton(text="◀️ На главную"))
    return builder.as_markup(resize_keyboard=True)

def get_main_keyboard(is_admin: bool = False):
    """Основная клавиатура"""
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📢 Разместить рекламу"))
    builder.row(
        types.KeyboardButton(text="📋 Мои объявления"),
        types.KeyboardButton(text="💰 Баланс")
    )
    builder.row(types.KeyboardButton(text="🆘 Помощь"))
    if is_admin:
        builder.row(types.KeyboardButton(text="👑 Админ-панель"))
    return builder.as_markup(resize_keyboard=True)

@admin_router.message(F.text == "👑 Админ-панель")
@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message, cleaner: MessageCleaner):
    """Главное меню админ-панели"""
    if not await is_admin(message.from_user.id):
        return await message.answer("⛔ Доступ запрещён!")
    
    await cleaner.clean_chat(message.bot, message.chat.id)
    await message.answer(
        "🛠️ <b>Админ-панель</b>\nВыберите действие:",
        reply_markup=get_admin_keyboard()
    )

@admin_router.message(F.text == "📈 Статистика")
async def show_stats(message: types.Message, cleaner: MessageCleaner):
    """Показать статистику бота"""
    if not await is_admin(message.from_user.id):
        return
    
    await cleaner.clean_chat(message.bot, message.chat.id)
    db = next(get_db())
    
    try:
        # Общая статистика
        total_users = db.scalar(select(func.count(User.id)))
        total_ads = db.scalar(select(func.count(Ad.id)))
        
        # Статистика за последние 24 часа
        day_ago = datetime.utcnow() - timedelta(days=1)
        new_users = db.scalar(select(func.count(User.id)).where(User.created_at >= day_ago))
        active_users = db.scalar(select(func.count(User.id)).where(User.last_activity >= day_ago))
        
        text = (
            "📊 <b>Статистика бота</b>\n\n"
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"🆕 Новых за сутки: <b>{new_users}</b>\n"
            f"🔥 Активных: <b>{active_users}</b>\n\n"
            f"📢 Всего объявлений: <b>{total_ads}</b>\n"
            f"⏳ На модерации: <b>{db.scalar(select(func.count(Ad.id)).where(Ad.status == 'pending'))}</b>"
        )
        
        await message.answer(text)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await message.answer("❌ Ошибка при получении статистики")

@admin_router.message(F.text == "📢 Рассылка")
async def start_broadcast(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Начать процесс рассылки"""
    if not await is_admin(message.from_user.id):
        return
    
    await cleaner.clean_chat(message.bot, message.chat.id)
    await message.answer(
        "📢 <b>Создание рассылки</b>\n"
        "Отправьте сообщение для рассылки (текст, фото или видео):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state("broadcast")

@admin_router.message(StateFilter("broadcast"))
async def process_broadcast(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Обработка рассылки"""
    db = next(get_db())
    users = db.scalars(select(User)).all()
    
    success = failed = 0
    progress_msg = await message.answer("⏳ Начинаю рассылку...")
    await cleaner.add_message(message.chat.id, progress_msg.message_id)
    
    for user in users:
        try:
            if message.photo:
                await message.bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                )
            elif message.video:
                await message.bot.send_video(
                    chat_id=user.telegram_id,
                    video=message.video.file_id,
                    caption=message.caption
                )
            else:
                await message.send_copy(user.telegram_id)
            success += 1
        except Exception as e:
            logger.error(f"Ошибка рассылки для {user.telegram_id}: {e}")
            failed += 1
        await asyncio.sleep(0.1)
    
    await progress_msg.edit_text(
        f"📢 <b>Рассылка завершена</b>\n\n"
        f"✅ Успешно: {success}\n"
        f"❌ Не удалось: {failed}"
    )
    await state.clear()
    await admin_panel(message, cleaner)

@admin_router.message(F.text == "✅ Модерация")
async def moderate_ads(message: types.Message, cleaner: MessageCleaner):
    """Модерация объявлений"""
    if not await is_admin(message.from_user.id):
        return
    
    await cleaner.clean_chat(message.bot, message.chat.id)
    db = next(get_db())
    
    ads = db.scalars(
        select(Ad)
        .where(Ad.status == "pending")
        .order_by(Ad.created_at.desc())
        .limit(5)
    ).all()
    
    if not ads:
        return await message.answer("ℹ️ Нет объявлений для модерации")
    
    builder = InlineKeyboardBuilder()
    for ad in ads:
        builder.row(
            types.InlineKeyboardButton(
                text=f"✅ Одобрить #{ad.id}",
                callback_data=f"approve_{ad.id}"),
            types.InlineKeyboardButton(
                text=f"❌ Отклонить #{ad.id}",
                callback_data=f"reject_{ad.id}")
        )
    
    builder.row(
        types.InlineKeyboardButton(
            text="🔄 Обновить список",
            callback_data="refresh_moderation")
    )
    
    msg = await message.answer(
        "⏳ <b>Ожидающие модерации:</b>\n"
        f"Найдено: {len(ads)}\n\n"
        "Последние 5 объявлений:",
        reply_markup=builder.as_markup()
    )
    await cleaner.add_message(message.chat.id, msg.message_id)

@admin_router.callback_query(F.data.startswith("approve_"))
async def approve_ad(callback: types.CallbackQuery, cleaner: MessageCleaner):
    """Одобрить объявление"""
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Доступ запрещён", show_alert=True)
    
    ad_id = int(callback.data.split("_")[1])
    db = next(get_db())
    
    try:
        ad = db.get(Ad, ad_id)
        if not ad:
            return await callback.answer("Объявление не найдено", show_alert=True)
        
        ad.status = "approved"
        ad.approved_at = datetime.utcnow()
        db.commit()
        
        try:
            await callback.bot.send_message(
                ad.user_id,
                f"✅ Ваше объявление #{ad.id} одобрено!\n"
                f"Канал: {ad.channel}\n"
                f"Срок: {ad.duration}\n\n"
                f"Текст: {ad.text[:200]}..."
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления: {e}")
        
        await callback.answer("Объявление одобрено")
        await moderate_ads(callback.message, cleaner)
    except Exception as e:
        logger.error(f"Ошибка модерации: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@admin_router.callback_query(F.data.startswith("reject_"))
async def reject_ad(callback: types.CallbackQuery, cleaner: MessageCleaner):
    """Отклонить объявление"""
    if not await is_admin(callback.from_user.id):
        return await callback.answer("Доступ запрещён", show_alert=True)
    
    ad_id = int(callback.data.split("_")[1])
    db = next(get_db())
    
    try:
        ad = db.get(Ad, ad_id)
        if not ad:
            return await callback.answer("Объявление не найдено", show_alert=True)
        
        ad.status = "rejected"
        db.commit()
        
        try:
            await callback.bot.send_message(
                ad.user_id,
                f"❌ Ваше объявление #{ad.id} отклонено\n"
                f"Причина: не соответствует правилам\n\n"
                f"Текст: {ad.text[:200]}..."
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления: {e}")
        
        await callback.answer("Объявление отклонено")
        await moderate_ads(callback.message, cleaner)
    except Exception as e:
        logger.error(f"Ошибка модерации: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@admin_router.callback_query(F.data == "refresh_moderation")
async def refresh_moderation(callback: types.CallbackQuery, cleaner: MessageCleaner):
    """Обновить список модерации"""
    await callback.answer("Обновляем список...")
    await moderate_ads(callback.message, cleaner)

@admin_router.message(F.text == "◀️ На главную")
async def back_to_main(message: types.Message, state: FSMContext, cleaner: MessageCleaner):
    """Вернуться в главное меню"""
    await state.clear()
    await cleaner.clean_chat(message.bot, message.chat.id)
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard(await is_admin(message.from_user.id))
    )