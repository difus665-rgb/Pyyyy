"""
Inline клавиатуры для бота
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
from utils.translator import t, get_available_languages


def get_messages_keyboard(messages: List[Dict], lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для списка писем"""
    keyboard = []
    
    for message in messages:
        message_id = message.get("id", "")
        subject = message.get("subject", "Без темы")
        sender = message.get("from", {}).get("address", "Неизвестный отправитель")
        
        # Ограничиваем длину текста на кнопке
        button_text = f"📧 {subject[:30]}..." if len(subject) > 30 else f"📧 {subject}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"view_message:{message_id}"
            )
        ])
    
    # Кнопка обновления списка
    keyboard.append([
        InlineKeyboardButton(
            text=t("refresh", lang),
            callback_data="refresh_inbox"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_message_actions_keyboard(message_id: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для действий с сообщением"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=t("back_to_inbox", lang),
                callback_data="back_to_inbox"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_email_management_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для управления почтой"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📧 " + t("btn_get_mail", lang),
                callback_data="create_email"
            )
        ],
        [
            InlineKeyboardButton(
                text="📬 " + t("btn_view_mails", lang),
                callback_data="check_messages"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑️ " + t("btn_delete", lang),
                callback_data="delete_email"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора языка"""
    available_languages = get_available_languages()
    keyboard = []
    
    for lang_code, lang_name in available_languages.items():
        keyboard.append([
            InlineKeyboardButton(
                text=lang_name,
                callback_data=f"set_language:{lang_code}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
