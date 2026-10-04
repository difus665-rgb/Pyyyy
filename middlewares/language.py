"""
Middleware для управления языком пользователя
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from utils.storage_utils import get_user_language


class LanguageMiddleware(BaseMiddleware):
    """Middleware для установки языка пользователя в контекст"""
    
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
        
        # Устанавливаем язык по умолчанию
        lang = "ru"
        
        if user_id:
            # Получаем язык пользователя из bot_storage
            lang = get_user_language(user_id)
        
        # Добавляем язык в контекст
        data['lang'] = lang
        
        # Продолжаем обработку
        return await handler(event, data)
