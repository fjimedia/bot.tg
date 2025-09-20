from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from config import settings
from config.states import States
from config.keyboard_layouts import get_main_menu
from services.payment import process_payment
from database.crud import create_ad
from database.session import get_db
from aiogram.types import ReplyKeyboardRemove
import logging

logger = logging.getLogger(__name__)
payment_router = Router(name='payment_router')

@payment_router.message(States.enter_text)
async def enter_ad_text(message: types.Message, state: FSMContext):
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        
        # Проверяем длину текста объявления
        if len(message.text) > 500:
            await message.answer("❌ Текст объявления слишком длинный (максимум 500 символов)")
            return
            
        if len(message.text) < 10:
            await message.answer("❌ Текст объявления слишком короткий (минимум 10 символов)")
            return

        # Создаем объявление в БД
        db = next(get_db())
        ad = create_ad(
            db,
            user_id=message.from_user.id,
            channel=data['channel'],
            text=message.text,
            price=data['price'],
            duration=data['duration']
        )

        # Обрабатываем платеж
        payment_result = await process_payment(
            user_id=message.from_user.id,
            channel=data['channel'],
            duration=data['duration'],
            amount=data['price']
        )

        if payment_result:
            await message.answer(
                "✅ Объявление успешно создано!\n"
                "Ожидайте подтверждения администратора.",
                reply_markup=get_main_menu(message.from_user.id in settings.ADMIN_IDS)
            )
            logger.info(f"New ad created: {ad.id} by user {message.from_user.id}")
        else:
            await message.answer(
                "❌ Ошибка при обработке платежа. Пожалуйста, попробуйте позже.",
                reply_markup=get_main_menu(message.from_user.id in settings.ADMIN_IDS)
            )
            logger.error(f"Payment failed for user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in enter_ad_text: {e}", exc_info=True)
        await message.answer(
            "⚠️ Произошла ошибка при обработке вашего запроса",
            reply_markup=get_main_menu(message.from_user.id in settings.ADMIN_IDS)
        )
    finally:
        # Всегда очищаем состояние
        await state.clear()
        db.close()