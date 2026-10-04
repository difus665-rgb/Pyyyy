"""
Роутер для команды изменения языка
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InaccessibleMessage
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

from utils.translator import t, get_available_languages
from utils.storage_utils import set_user_language
from keyboards.builders import get_main_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("language"))
async def cmd_language(message: Message, lang: str = "ru"):
    """Обработчик команды /language"""
    if not message.from_user:
        await message.answer(t("error_user", lang))
        return
    
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запросил смену языка")
    
    # Создаем клавиатуру с доступными языками
    available_languages = get_available_languages()
    keyboard = []
    
    for lang_code, lang_name in available_languages.items():
        keyboard.append([
            InlineKeyboardButton(
                text=lang_name,
                callback_data=f"set_language:{lang_code}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        t("language_select", lang),
        reply_markup=reply_markup
    )


@router.callback_query(F.data.startswith("set_language:"))
async def callback_set_language(callback: CallbackQuery, lang: str = "ru"):
    """Обработчик выбора языка"""
    if not callback.from_user or not callback.data or not callback.message:
        await callback.answer(t("error_user", lang))
        return
    
    user_id = callback.from_user.id
    new_lang = callback.data.split(":", 1)[1]
    
    logger.info(f"Пользователь {user_id} выбрал язык: {new_lang}")
    
    # Проверяем валидность языка
    available_languages = get_available_languages()
    if new_lang not in available_languages:
        await callback.answer(t("error", new_lang))
        return    # Обновляем язык пользователя в bot_storage
    success = set_user_language(user_id, new_lang)
    
    if success:
        # Уведомляем об успешной смене языка на новом языке
        success_message = t("language_changed", new_lang)
        
        try:
            if callback.message and not isinstance(callback.message, InaccessibleMessage):
                # Показываем приветственное сообщение на новом языке
                await callback.message.edit_text(
                    t("start", new_lang),
                    reply_markup=None  # Убираем inline клавиатуру
                )
                # Отправляем основную клавиатуру отдельным сообщением
                await callback.message.answer(
                    t("language_changed", new_lang),
                    reply_markup=get_main_keyboard(new_lang)
                )
            else:
                await callback.answer(success_message)
        except TelegramBadRequest:
            await callback.answer(success_message)
            # Отправляем новое сообщение с приветствием
            if callback.message:
                await callback.message.answer(
                    t("start", new_lang),
                    reply_markup=get_main_keyboard(new_lang)
                )
        
    else:
        await callback.answer(t("error", lang))
        logger.error(f"Failed to update language for user {user_id}")
