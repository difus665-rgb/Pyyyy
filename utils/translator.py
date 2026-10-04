"""
Утилиты для работы с переводами и локализацией
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Загружаем локали
LOCALES: Dict[str, Dict[str, str]] = {}

def load_locales():
    """Загрузка файлов локализации"""
    global LOCALES
    
    locales_dir = Path("locales")
    if not locales_dir.exists():
        logger.warning("Locales directory not found")
        return
    
    for locale_file in locales_dir.glob("*.json"):
        lang_code = locale_file.stem
        try:
            with open(locale_file, "r", encoding="utf-8") as f:
                LOCALES[lang_code] = json.load(f)
            logger.info(f"Loaded locale: {lang_code}")
        except Exception as e:
            logger.error(f"Failed to load locale {lang_code}: {e}")

# Загружаем локали при импорте модуля
load_locales()

def t(key: str, lang: str = "ru", **kwargs) -> str:
    """
    Получить переведенную строку
    
    :param key: Ключ перевода
    :param lang: Код языка (ru, en)
    :param kwargs: Параметры для форматирования строки
    :return: Переведенная строка
    """
    # Получаем словарь для языка
    locale_dict = LOCALES.get(lang, {})
    
    # Получаем шаблон строки
    template = locale_dict.get(key, key)
    
    # Если ключ не найден в выбранном языке, пробуем русский
    if template == key and lang != "ru":
        template = LOCALES.get("ru", {}).get(key, key)
    
    # Форматируем строку с параметрами
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError) as e:
        logger.warning(f"Failed to format translation key '{key}' with kwargs {kwargs}: {e}")
        return template

def get_available_languages() -> Dict[str, str]:
    """Получить список доступных языков"""
    return {
        "ru": "🇷🇺 Русский",
        "en": "🇬🇧 English"
    }
