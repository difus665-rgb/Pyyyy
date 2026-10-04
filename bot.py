#!/usr/bin/env python3
"""
Telegram Bot с временной почтой
Этап 1 - Базовая структура команд и интерфейсов
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config.settings import settings
from routers import commands, language, admin
from middlewares import ThrottlingMiddleware, LanguageMiddleware, BanMiddleware
from utils.logger import setup_logging
from utils.translator import load_locales


async def register_commands(bot: Bot):
    """Регистрация команд бота"""
    commands_list = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="📖 Показать справку"),
        BotCommand(command="newmail", description="📧 Создать новую почту"),
        BotCommand(command="inbox", description="📬 Просмотреть письма"),
        BotCommand(command="delete", description="🗑️ Удалить почту"),
        BotCommand(command="language", description="🌐 Изменить язык"),
        BotCommand(command="admin", description="🔐 Админ-панель"),
        BotCommand(command="stats", description="📊 Статистика бота"),
        BotCommand(command="broadcast", description="📤 Рассылка сообщений"),
        BotCommand(command="ban", description="🚫 Заблокировать пользователя"),
    ]
    
    await bot.set_my_commands(commands_list)
    logger = logging.getLogger(__name__)
    logger.info("Команды бота зарегистрированы")


async def main():
    """Главная функция запуска бота"""
    # Настройка логирования
    setup_logging()
    
    # Загрузка локалей
    load_locales()
    
    logger = logging.getLogger(__name__)
    logger.info("Запуск бота...")
    
    # Инициализация бота и диспетчера
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Регистрация команд
    await register_commands(bot)
    
    dp = Dispatcher()
    
    # Подключение middlewares
    # Ban middleware - должен быть первым для блокировки пользователей
    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())
    
    # Throttling middleware для антиспама (2 секунды между сообщениями)
    dp.message.middleware(ThrottlingMiddleware(rate_limit=2.0))
    
    # Language middleware для определения языка пользователя
    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())
    
    # Подключение роутеров (порядок важен!)
    dp.include_router(admin.router)    # Админ роутер должен быть первым
    dp.include_router(language.router) # Роутер языка
    dp.include_router(commands.router) # Основные команды
    
    logger.info("Бот успешно инициализирован")
    
    # Запуск бота (Aiogram сам перехватывает SIGINT/SIGTERM и безопасно завершает работу)
    try:
        logger.info("Бот запущен и готов к работе! Нажмите Ctrl+C для остановки.")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        logger.info("Закрытие сессии бота...")
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен вручную")