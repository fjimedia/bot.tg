from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import types
from config.settings import settings

def admin_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text="📈 Статистика"),
        types.KeyboardButton(text="📢 Создать рассылку"),
        types.KeyboardButton(text="✅ Одобрить объявления")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_main_menu(is_admin: bool = False):
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="📢 Разместить рекламу"),
        types.KeyboardButton(text="📋 Мои объявления")
    )
    builder.row(
        types.KeyboardButton(text="💰 Баланс"),
        types.KeyboardButton(text="🆘 Помощь")
    )
    if is_admin:
        builder.row(types.KeyboardButton(text="👑 Админ-панель"))
    return builder.as_markup(resize_keyboard=True)

def generate_channels_kb():
    builder = ReplyKeyboardBuilder()
    for channel in settings.CHANNELS:
        builder.add(types.KeyboardButton(text=channel))
    builder.add(types.KeyboardButton(text="◀️ Назад"))
    return builder.as_markup(resize_keyboard=True)

def generate_durations_kb():
    builder = ReplyKeyboardBuilder()
    for duration in settings.PRICES:
        builder.add(types.KeyboardButton(text=duration))
    builder.add(types.KeyboardButton(text="◀️ Назад"))
    return builder.as_markup(resize_keyboard=True)
def get_main_kb(user_id: int):
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📢 Разместить рекламу"))
    builder.row(types.KeyboardButton(text="🔙 Назад"))  # Добавили кнопку
    return builder.as_markup(resize_keyboard=True)