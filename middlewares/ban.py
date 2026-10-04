"""
Middleware для проверки заблокированных пользователей
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from utils.storage_utils import load_bot_data


class BanMiddleware(BaseMiddleware):
    """Middleware для блокировки заблокированных пользователей"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Основная логика middleware"""
        
        # Получаем user_id из разных типов событий
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            if event.from_user:
                user_id = event.from_user.id
        
        # Если пользователь не определен, пропускаем проверку
        if not user_id:
            return await handler(event, data)
        
        # Проверяем, заблокирован ли пользователь
        bot_data = load_bot_data()
        banned_users = bot_data.get('banned', [])
        
        if user_id in banned_users:
            # Пользователь заблокирован, не обрабатываем его сообщения
            if isinstance(event, Message):
                await event.answer("🚫 Вы заблокированы и не можете использовать этого бота.")
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Вы заблокированы.", show_alert=True)
            return
        
        # Продолжаем обработку
        return await handler(event, data)
