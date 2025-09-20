from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import types
from config.settings import settings
def get_main_menu(is_admin: bool = False):
    builder = ReplyKeyboardBuilder()
    menu_items = [
        ("📢 Разместить рекламу", "Создать новое объявление"),
        ("📋 Мои объявления", "Ваши активные объявления"),
        ("💰 Баланс", "Пополнение и история платежей"),
        ("🆘 Помощь", "Инструкции и поддержка")
    ]
    
    for btn, _ in menu_items:
        builder.add(types.KeyboardButton(text=btn))
    builder.adjust(2, 2)
    
    if is_admin:
        builder.row(types.KeyboardButton(text="👑 Админ-панель"))
    
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
def generate_channels_kb():
    builder = ReplyKeyboardBuilder()
    # Добавление кнопок каналов...
    builder.row(types.KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)