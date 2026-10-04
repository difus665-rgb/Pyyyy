"""
Конструкторы клавиатур для бота
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.translator import t


def get_main_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Основная reply-клавиатура с кнопками управления"""
    keyboard = [[
        KeyboardButton(text=t("btn_get_mail", lang)),
        KeyboardButton(text=t("btn_view_mails", lang))
    ], [
        KeyboardButton(text=t("btn_delete", lang))
    ]]
    return ReplyKeyboardMarkup(
        keyboard=keyboard, 
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_admin_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Админская reply-клавиатура"""
    keyboard = [[
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="📤 Рассылка")
    ], [
        KeyboardButton(text="🚫 Забанить пользователя"),
        KeyboardButton(text="🔙 Назад")
    ]]
    return ReplyKeyboardMarkup(
        keyboard=keyboard, 
        resize_keyboard=True,
        one_time_keyboard=False
    )
