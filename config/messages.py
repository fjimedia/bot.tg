from dataclasses import dataclass

@dataclass
class Messages:
    START: str = "👋 Добро пожаловать в рекламного бота!"
    CHANNEL_CHOICE: str = "📢 Выберите канал для рекламы:"
    ADMIN_PANEL: str = "👑 Админ-панель"
    PAYMENT_INFO: str = "💳 Выберите способ оплаты:"
    
    @staticmethod
    def price_info(price: int, discount: int) -> str:
        return f"💵 Цена: {price} руб.\n🎁 Скидка: {discount}%"

messages = Messages()