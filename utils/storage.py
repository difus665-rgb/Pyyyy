"""
Утилиты для работы с пользовательскими данными
"""

import json
import logging
import os
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

STORAGE_FILE = "storage/bot_storage.json"


class UserStorage:
    """Класс для работы с пользовательскими данными"""
    
    def __init__(self):
        self.storage_path = STORAGE_FILE
        self._ensure_storage_exists()
        
    def _ensure_storage_exists(self):
        """Убедиться что файл хранилища существует"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            self._save_data({})
            
    def _load_data(self) -> Dict[str, Any]:
        """Загрузка данных из файла"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading storage data: {e}")
            return {}
            
    def _save_data(self, data: Dict[str, Any]):
        """Сохранение данных в файл"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving storage data: {e}")
            
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных пользователя"""
        data = self._load_data()
        return data.get(str(user_id))
        
    def set_user_data(self, user_id: int, user_data: Dict[str, Any]):
        """Сохранение данных пользователя"""
        data = self._load_data()
        data[str(user_id)] = user_data
        self._save_data(data)
        
    def delete_user_data(self, user_id: int):
        """Удаление данных пользователя"""
        data = self._load_data()
        if str(user_id) in data:
            del data[str(user_id)]
            self._save_data(data)
            
    def get_user_email_data(self, user_id: int) -> Optional[Dict[str, str]]:
        """Получение email данных пользователя"""
        user_data = self.get_user_data(user_id)
        if user_data and 'email_data' in user_data:
            return user_data['email_data']
        return None
        
    def set_user_email_data(self, user_id: int, email: str, password: str, 
                           token: str, account_id: str):
        """Сохранение email данных пользователя"""
        user_data = self.get_user_data(user_id) or {}
        user_data['email_data'] = {
            'email': email,
            'password': password,
            'token': token,
            'account_id': account_id
        }
        self.set_user_data(user_id, user_data)
        
    def clear_user_email_data(self, user_id: int):
        """Очистка email данных пользователя"""
        user_data = self.get_user_data(user_id) or {}
        if 'email_data' in user_data:
            del user_data['email_data']
            self.set_user_data(user_id, user_data)


# Глобальный экземпляр хранилища
storage = UserStorage()
