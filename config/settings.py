import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Dict, Any

class Settings(BaseSettings):
    # Основные настройки
    BOT_TOKEN: str = Field(..., min_length=10, description="Telegram Bot Token")
    ADMIN_IDS: List[int] = Field(default=[], description="Admin Telegram IDs")
    DATABASE_URL: str = Field(
        default="sqlite:///./database.db",
        description="Database connection URL"
    )
    REDIS_URL: str = "redis://localhost:6379/0"  # Значение по умолчанию
    
    # Настройки каналов
    CHANNELS: Dict[str, Dict[str, Any]] = Field(
        default={
            "Китайский для ума": {
                "id": "@cleverchinese",
                "url": "https://t.me/cleverchinese",
                "price_multiplier": 1.0
            },
            "Explore China": {
                "id": "@explorezhongguo",
                "url": "https://t.me/explorezhongguo",
                "price_multiplier": 1.0
            }
        },
        description="Channels available for advertising"
    )
    
    # Настройки цен
    PRICES: Dict[str, Dict[str, int]] = Field(
        default={
            "1 день": {"price": 1000, "discount": 0},
            "2 дня": {"price": 1800, "discount": 0},
            "неделя": {"price": 5000, "discount": 0}
        },
        description="Pricing information"
    )

    # Валидаторы
    @field_validator('ADMIN_IDS', mode='before')
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(id.strip()) for id in v.split(',') if id.strip().isdigit()]
        return v or []

    # Конфигурация
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

# Проверка существования .env
if not os.path.exists(".env"):
    raise FileNotFoundError(
        "Создайте файл .env в папке проекта со следующими переменными:\n"
        "BOT_TOKEN=ваш_токен\n"
        "ADMIN_IDS=ваш_id\n"
        "DATABASE_URL=sqlite:///./database.db\n"
        "# Опционально:\n"
        "# CHANNELS={\"Канал 1\": {\"id\": \"@channel1\"}}\n"
        "# PRICES={\"1 день\": {\"price\": 1000}}"
    )

settings = Settings()