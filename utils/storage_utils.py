"""
Утилиты для работы с локальным хранилищем пользователей
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

STORAGE_FILE = "storage/user_storage.json"
BOT_STORAGE_FILE = "storage/bot_storage.json"


def _ensure_storage_dir():
    """Убедиться, что директория storage существует"""
    os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)


def load_data() -> Dict[str, Dict[str, Any]]:
    """Загружает данные из JSON файла"""
    _ensure_storage_dir()
    
    if not os.path.exists(STORAGE_FILE):
        logger.info(f"Storage file {STORAGE_FILE} doesn't exist, creating empty storage")
        return {}
    
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} users from storage")
            return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading storage: {e}")
        return {}


def save_data(data: Dict[str, Dict[str, Any]]) -> bool:
    """Сохраняет данные в JSON файл"""
    _ensure_storage_dir()
    
    try:
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} users to storage")
        return True
    except Exception as e:
        logger.error(f"Error saving storage: {e}")
        return False


def load_bot_data() -> Dict[str, Any]:
    """Загружает данные бота из JSON файла"""
    _ensure_storage_dir()
    
    if not os.path.exists(BOT_STORAGE_FILE):
        logger.info(f"Bot storage file {BOT_STORAGE_FILE} doesn't exist, creating empty storage")
        return {"user_languages": {}}
    
    try:
        with open(BOT_STORAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded bot data from storage")
            return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading bot storage: {e}")
        return {"user_languages": {}}


def save_bot_data(data: Dict[str, Any]) -> bool:
    """Сохраняет данные бота в JSON файл"""
    _ensure_storage_dir()
    
    try:
        with open(BOT_STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved bot data to storage")
        return True
    except Exception as e:
        logger.error(f"Error saving bot storage: {e}")
        return False


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Получает данные пользователя"""
    data = load_data()
    user_data = data.get(str(user_id))
    
    if user_data:
        logger.info(f"Retrieved user {user_id}: email={user_data.get('email', 'N/A')}")
    else:
        logger.info(f"User {user_id} not found in storage")
    
    return user_data


def update_user(user_id: int, **kwargs) -> bool:
    """Обновляет данные пользователя"""
    data = load_data()
    user_key = str(user_id)
    
    if user_key not in data:
        data[user_key] = {}
    
    # Добавляем время последнего обновления
    kwargs['updated_at'] = datetime.now().isoformat()
    
    # Если это новый пользователь, добавляем время создания
    if 'created_at' not in data[user_key]:
        kwargs['created_at'] = datetime.now().isoformat()
    
    data[user_key].update(kwargs)
    
    success = save_data(data)
    if success:
        logger.info(f"Updated user {user_id} with data: {list(kwargs.keys())}")
    
    return success


def delete_user(user_id: int) -> bool:
    """Удаляет пользователя из хранилища"""
    data = load_data()
    user_key = str(user_id)
    
    if user_key in data:
        email = data[user_key].get('email', 'unknown')
        del data[user_key]
        success = save_data(data)
        if success:
            logger.info(f"Deleted user {user_id} (email: {email})")
        return success
    else:
        logger.warning(f"User {user_id} not found for deletion")
        return False


def user_exists(user_id: int) -> bool:
    """Проверяет, существует ли пользователь в хранилище"""
    return get_user(user_id) is not None


def get_user_email(user_id: int) -> Optional[str]:
    """Получает email пользователя"""
    user_data = get_user(user_id)
    return user_data.get('email') if user_data else None


def get_user_token(user_id: int) -> Optional[str]:
    """Получает токен пользователя"""
    user_data = get_user(user_id)
    return user_data.get('token') if user_data else None


def get_all_users() -> Dict[str, Dict[str, Any]]:
    """Получает всех пользователей (для административных целей)"""
    return load_data()


def cleanup_old_users(days: int = 7) -> int:
    """Удаляет пользователей старше указанного количества дней"""
    from datetime import datetime, timedelta
    
    data = load_data()
    cutoff_date = datetime.now() - timedelta(days=days)
    users_to_delete = []
    
    for user_id, user_data in data.items():
        created_at_str = user_data.get('created_at')
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str)
                if created_at < cutoff_date:
                    users_to_delete.append(user_id)
            except ValueError:
                logger.warning(f"Invalid date format for user {user_id}: {created_at_str}")
    
    for user_id in users_to_delete:
        del data[user_id]
    
    if users_to_delete:
        save_data(data)
        logger.info(f"Cleaned up {len(users_to_delete)} old users")
    
    return len(users_to_delete)


def get_user_language(user_id: int) -> str:
    """Получает язык пользователя из bot_storage"""
    data = load_bot_data()
    return data.get("user_languages", {}).get(str(user_id), "ru")


def set_user_language(user_id: int, language: str) -> bool:
    """Устанавливает язык пользователя в bot_storage"""
    data = load_bot_data()
    
    if "user_languages" not in data:
        data["user_languages"] = {}
    
    data["user_languages"][str(user_id)] = language
    
    success = save_bot_data(data)
    if success:
        logger.info(f"Set language for user {user_id}: {language}")
    
    return success


def get_bot_stats() -> Dict[str, Any]:
    """Получает статистику бота из bot_storage"""
    data = load_bot_data()
    
    if "stats" not in data:
        data["stats"] = {
            "total_users": 0,
            "created_emails": 0,
            "total_broadcasts": 0,
            "created_at": datetime.now().isoformat()
        }
        save_bot_data(data)
    
    return data["stats"]


def update_bot_stats(stats: Dict[str, Any]) -> bool:
    """Обновляет статистику бота в bot_storage"""
    data = load_bot_data()
    
    if "stats" not in data:
        data["stats"] = {}
    
    data["stats"].update(stats)
    data["stats"]["updated_at"] = datetime.now().isoformat()
    
    success = save_bot_data(data)
    if success:
        logger.info(f"Updated bot stats: {list(stats.keys())}")
    
    return success


def get_banned_users() -> list:
    """Получает список заблокированных пользователей"""
    data = load_bot_data()
    return data.get("banned_users", [])


def add_banned_user(user_id: int) -> bool:
    """Добавляет пользователя в список заблокированных"""
    data = load_bot_data()
    
    if "banned_users" not in data:
        data["banned_users"] = []
    
    if user_id not in data["banned_users"]:
        data["banned_users"].append(user_id)
        
        success = save_bot_data(data)
        if success:
            logger.info(f"Added user {user_id} to banned list")
        return success
    else:
        logger.warning(f"User {user_id} is already banned")
        return True


def remove_banned_user(user_id: int) -> bool:
    """Удаляет пользователя из списка заблокированных"""
    data = load_bot_data()
    
    if "banned_users" not in data:
        data["banned_users"] = []
    
    if user_id in data["banned_users"]:
        data["banned_users"].remove(user_id)
        
        success = save_bot_data(data)
        if success:
            logger.info(f"Removed user {user_id} from banned list")
        return success
    else:
        logger.warning(f"User {user_id} is not in banned list")
        return True


def is_user_banned(user_id: int) -> bool:
    """Проверяет, заблокирован ли пользователь"""
    banned_users = get_banned_users()
    return user_id in banned_users


def add_broadcast_record(record: Dict[str, Any]) -> bool:
    """Добавляет запись о рассылке в bot_storage"""
    data = load_bot_data()
    
    if "broadcasts" not in data:
        data["broadcasts"] = []
    
    data["broadcasts"].append(record)
    
    # Обновляем статистику
    if "stats" not in data:
        data["stats"] = {"total_broadcasts": 0}
    
    data["stats"]["total_broadcasts"] = data["stats"].get("total_broadcasts", 0) + 1
    
    success = save_bot_data(data)
    if success:
        logger.info(f"Added broadcast record by admin {record.get('admin_id')}")
    
    return success


def get_broadcast_history() -> list:
    """Получает историю рассылок"""
    data = load_bot_data()
    return data.get("broadcasts", [])


def increment_email_counter() -> bool:
    """Увеличивает счетчик созданных email-адресов"""
    data = load_bot_data()
    
    if "stats" not in data:
        data["stats"] = {"created_emails": 0}
    
    data["stats"]["created_emails"] = data["stats"].get("created_emails", 0) + 1
    
    success = save_bot_data(data)
    if success:
        logger.info("Incremented email counter")
    
    return success
