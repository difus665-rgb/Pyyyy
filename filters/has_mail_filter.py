"""
Фильтр для проверки наличия активной почты у пользователя
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Union

from utils.storage_utils import get_user


class HasMailFilter(BaseFilter):
    """Фильтр для проверки, есть ли у пользователя активная почта"""
    
    def __init__(self, has_mail: bool = True):
        """
        :param has_mail: True - проверить что есть почта, False - проверить что нет почты
        """
        self.has_mail = has_mail
    
    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        """
        Проверяет наличие активной почты у пользователя
        
        :param obj: Объект сообщения или callback query
        :return: True если условие выполнено, False иначе
        """
        if not obj.from_user:
            return False
            
        user_id = obj.from_user.id
        user_data = get_user(user_id)
        
        # Проверяем наличие активной почты
        has_active_mail = bool(user_data and user_data.get('email') and user_data.get('token'))
        
        # Возвращаем результат в зависимости от требуемого условия
        return has_active_mail if self.has_mail else not has_active_mail


# Создаем экземпляры фильтров
has_mail = HasMailFilter(has_mail=True)
no_mail = HasMailFilter(has_mail=False)
