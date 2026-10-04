"""
Middleware для ограничения частоты сообщений (антиспам)
"""

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message

from utils.translator import t
from utils.storage_utils import get_user


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты использования команд"""
    
    def __init__(self, rate_limit: float = 2.0):
        """
        :param rate_limit: Минимальное время между сообщениями в секундах
        """
        self.rate_limit = rate_limit
        self.user_timings: Dict[int, float] = {}
        
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Основная логика middleware"""
        
        # Проверяем только сообщения
        if not isinstance(event, Message):
            return await handler(event, data)
        
        # Проверяем, есть ли пользователь
        if not event.from_user:
            return await handler(event, data)
            
        user_id = event.from_user.id
        current_time = time.time()
          # Проверяем время последнего сообщения пользователя
        if user_id in self.user_timings:
            time_passed = current_time - self.user_timings[user_id]
            
            if time_passed < self.rate_limit:
                # Пользователь отправляет сообщения слишком часто
                remaining_time = self.rate_limit - time_passed
                
                # Получаем язык пользователя
                lang = "ru"  # По умолчанию
                if user_id:
                    user_data = get_user(user_id)
                    if user_data and user_data.get('lang'):
                        lang = user_data['lang']
                
                await event.answer(
                    t("throttling_message", lang, remaining_time=remaining_time)
                )
                return
        
        # Обновляем время последнего сообщения
        self.user_timings[user_id] = current_time
        
        # Очищаем старые записи (старше 1 часа)
        cutoff_time = current_time - 3600
        self.user_timings = {
            uid: timestamp 
            for uid, timestamp in self.user_timings.items() 
            if timestamp > cutoff_time
        }
        
        # Продолжаем обработку
        return await handler(event, data)
