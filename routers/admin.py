"""
Роутер для администраторских команд
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from filters import is_admin
from keyboards.builders import get_admin_keyboard
from utils.storage_utils import (
    get_bot_stats, update_bot_stats, add_banned_user, 
    get_banned_users, add_broadcast_record, get_all_users
)
from utils.translator import t

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("admin"), is_admin)
async def cmd_admin(message: Message, lang: str = "ru"):
    """Команда для доступа к админ-панели"""
    user_id = message.from_user.id if message.from_user else 0
    logger.info(f"Администратор {user_id} открыл админ-панель")
    
    await message.answer(
        "🔐 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=get_admin_keyboard(lang)
    )


@router.message(Command("stats"), is_admin)
async def cmd_stats(message: Message, lang: str = "ru"):
    """Команда для просмотра статистики"""
    user_id = message.from_user.id if message.from_user else 0
    logger.info(f"Администратор {user_id} запросил статистику")
    
    try:
        # Получаем статистику из bot_storage
        stats = get_bot_stats()
        
        # Подсчитываем активные сессии (пользователи с email)
        all_users = get_all_users()
        active_sessions = sum(1 for user_data in all_users.values() if user_data.get('email'))
        
        # Обновляем статистику
        stats['total_users'] = len(all_users)
        update_bot_stats(stats)
        
        stats_text = f"""📊 <b>Статистика бота</b>

👥 <b>Общее число пользователей:</b> {stats.get('total_users', 0)}
📧 <b>Создано email адресов:</b> {stats.get('created_emails', 0)}
🟢 <b>Активные сессии:</b> {active_sessions}
🚫 <b>Заблокированные пользователи:</b> {len(get_banned_users())}

📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
        
        await message.answer(stats_text)
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer("❌ Ошибка при получении статистики")


@router.message(Command("broadcast"), is_admin)
async def cmd_broadcast(message: Message, lang: str = "ru"):
    """Команда для рассылки сообщений"""
    user_id = message.from_user.id if message.from_user else 0
    
    # Получаем текст после команды
    if not message.text:
        await message.answer("❌ Сообщение не содержит текста")
        return
        
    text_parts = message.text.split(' ', 1)
    if len(text_parts) < 2:
        await message.answer("❌ Использование: /broadcast <текст сообщения>")
        return
    
    broadcast_text = text_parts[1]
    logger.info(f"Администратор {user_id} начал рассылку: {broadcast_text[:50]}...")
    
    try:
        # Получаем всех пользователей
        all_users = get_all_users()
        
        if not all_users:
            await message.answer("❌ Нет пользователей для рассылки")
            return
        
        await message.answer(f"📤 Начинаю рассылку для {len(all_users)} пользователей...")
        
        sent_count = 0
        failed_count = 0
        
        # Отправляем сообщение каждому пользователю
        for user_id_str in all_users.keys():
            try:
                target_user_id = int(user_id_str)
                if message.bot:
                    await message.bot.send_message(target_user_id, broadcast_text)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение пользователю {user_id_str}: {e}")
                failed_count += 1
        
        # Сохраняем запись о рассылке
        broadcast_record = {
            "date": datetime.now().isoformat(),
            "admin_id": user_id,
            "text": broadcast_text,
            "sent": sent_count,
            "failed": failed_count
        }
        add_broadcast_record(broadcast_record)
        
        result_text = f"""✅ <b>Рассылка завершена</b>

📤 <b>Отправлено:</b> {sent_count}
❌ <b>Не удалось отправить:</b> {failed_count}
📝 <b>Текст:</b> {broadcast_text[:100]}{'...' if len(broadcast_text) > 100 else ''}"""
        
        await message.answer(result_text)
        logger.info(f"Рассылка завершена: {sent_count} отправлено, {failed_count} неудачно")
        
    except Exception as e:
        logger.error(f"Ошибка при рассылке: {e}")
        await message.answer("❌ Ошибка при выполнении рассылки")


@router.message(Command("ban"), is_admin)
async def cmd_ban(message: Message, lang: str = "ru"):
    """Команда для блокировки пользователя"""
    admin_id = message.from_user.id if message.from_user else 0
    
    # Получаем user_id после команды
    if not message.text:
        await message.answer("❌ Сообщение не содержит текста")
        return
        
    text_parts = message.text.split(' ', 1)
    if len(text_parts) < 2:
        await message.answer("❌ Использование: /ban <user_id>")
        return
    
    try:
        target_user_id = int(text_parts[1])
    except ValueError:
        await message.answer("❌ Неверный формат user_id. Должно быть число.")
        return
    
    logger.info(f"Администратор {admin_id} заблокировал пользователя {target_user_id}")
    
    try:
        # Проверяем, не заблокирован ли уже пользователь
        banned_users = get_banned_users()
        if target_user_id in banned_users:
            await message.answer(f"⚠️ Пользователь {target_user_id} уже заблокирован")
            return
        
        # Добавляем пользователя в бан-лист
        success = add_banned_user(target_user_id)
        
        if success:
            await message.answer(f"🚫 Пользователь {target_user_id} заблокирован")
            
            # Пытаемся уведомить пользователя о блокировке
            try:
                if message.bot:
                    await message.bot.send_message(
                        target_user_id,
                        "🚫 Вы были заблокированы администратором. Обратитесь в поддержку."
                    )
            except Exception:
                # Игнорируем ошибки отправки уведомления
                pass
        else:
            await message.answer("❌ Ошибка при блокировке пользователя")
            
    except Exception as e:
        logger.error(f"Ошибка при блокировке пользователя {target_user_id}: {e}")
        await message.answer("❌ Ошибка при выполнении команды")


# Обработчики кнопок админ-панели
@router.message(F.text == "📊 Статистика", is_admin)
async def handle_stats_button(message: Message, lang: str = "ru"):
    """Обработчик кнопки статистики"""
    await cmd_stats(message, lang)


@router.message(F.text == "📤 Рассылка", is_admin)
async def handle_broadcast_button(message: Message, lang: str = "ru"):
    """Обработчик кнопки рассылки"""
    await message.answer(
        "📤 <b>Рассылка сообщений</b>\n\n"
        "Для отправки рассылки используйте команду:\n"
        "<code>/broadcast ваш текст сообщения</code>"
    )


@router.message(F.text == "🚫 Забанить пользователя", is_admin)
async def handle_ban_button(message: Message, lang: str = "ru"):
    """Обработчик кнопки блокировки"""
    await message.answer(
        "🚫 <b>Блокировка пользователя</b>\n\n"
        "Для блокировки пользователя используйте команду:\n"
        "<code>/ban user_id</code>\n\n"
        "Пример: <code>/ban 123456789</code>"
    )


@router.message(F.text == "🔙 Назад", is_admin)
async def handle_back_button(message: Message, lang: str = "ru"):
    """Обработчик кнопки возврата"""
    from keyboards.builders import get_main_keyboard
    await message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_keyboard(lang)
    )
