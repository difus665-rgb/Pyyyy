"""
Фильтр для проверки прав администратора
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Union

from config.settings import settings


class AdminFilter(BaseFilter):
    """Фильтр для проверки, является ли пользователь администратором"""
    
    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        """
        Проверяет, является ли пользователь администратором
        
        :param obj: Объект сообщения или callback query
        :return: True если пользователь админ, False иначе
        """
        if not obj.from_user:
            return False
            
        user_id = obj.from_user.id
        admin_ids = settings.admin_ids_list
        
        return user_id in admin_ids


# Создаем экземпляр фильтра
is_admin = AdminFilter()
