"""
Роутер для обработки команд бота с поддержкой переводов
"""

import logging
import random
import string
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InaccessibleMessage
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from keyboards.builders import get_main_keyboard
from keyboards.inline import get_messages_keyboard, get_message_actions_keyboard
from services.api_client import MailGwClient
from utils.storage_utils import get_user, update_user, delete_user
from utils.translator import t
from filters import has_mail, no_mail
from states import MailStates

# Переменная router обязательна для регистрации в bot.py
router = Router()
logger = logging.getLogger(__name__)


def get_user_id(message: Message) -> str:
    """Получить ID пользователя или 'Unknown' если пользователь не определен"""
    return str(message.from_user.id) if message.from_user else "Unknown"


def generate_password(length: int = 12) -> str:
    """Генерация случайного пароля"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))


@router.message(Command("start"))
async def cmd_start(message: Message, lang: str = "ru"):
    """Обработчик команды /start"""
    user_id = get_user_id(message)
    logger.info(f"Пользователь {user_id} запустил бота")
    
    # Всегда показываем выбор языка при команде /start для всех пользователей
    if message.from_user:
        from keyboards.inline import get_language_keyboard
        await message.answer(
            "🌐 <b>Welcome! Добро пожаловать!</b>\n\nPlease choose your language / Выберите язык:",
            reply_markup=get_language_keyboard()
        )
    else:
        await message.answer(
            t("start", lang),
            reply_markup=get_main_keyboard(lang)
        )


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str = "ru"):
    """Обработчик команды /help"""
    user_id = get_user_id(message)
    logger.info(f"Пользователь {user_id} запросил помощь")
    
    await message.answer(t("help", lang))


@router.message(Command("newmail"))
async def cmd_newmail(message: Message, state: FSMContext, lang: str = "ru"):
    """Обработчик команды /newmail"""
    user_id = get_user_id(message)
    logger.info(f"Пользователь {user_id} запросил создание новой почты")
    
    if not message.from_user:
        await message.answer(t("error_user", lang))
        return
    
    # Проверяем, есть ли уже активная почта
    existing_user = get_user(message.from_user.id)
    if existing_user and existing_user.get('email'):
        # Показываем подтверждение для замены существующей почты
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=t("confirm_yes", lang), callback_data="confirm_new_email"),
                InlineKeyboardButton(text=t("confirm_no", lang), callback_data="cancel_new_email")
            ]
        ])
        
        await message.answer(
            t("mail_exists", lang, email=existing_user['email']),
            reply_markup=keyboard
        )
        await state.set_state(MailStates.confirm_replacement)
        return
    
    # Создаем новую почту
    await create_new_email(message, state, lang)


async def create_new_email(message: Message, state: FSMContext, lang: str = "ru"):
    """Создание новой временной почты"""
    user_id = get_user_id(message)
    
    if not message.from_user:
        await message.answer(t("error_user", lang))
        return
    
    await message.answer(t("mail_creating", lang))
    
    async with MailGwClient() as client:
        try:
            # Генерируем email
            email_data = await client.generate_email()
            if not email_data:
                await message.answer(t("error_connection", lang))
                return
            
            # Извлекаем данные
            email_str = email_data["email"] if isinstance(email_data, dict) else email_data
            sid_token = email_data.get("sid_token", email_str) if isinstance(email_data, dict) else email_str
            
            password = generate_password()
            account_id = email_str
            
            # Сохраняем данные пользователя
            success = update_user(
                message.from_user.id,
                email=email_str,
                password=password,
                token=sid_token,
                account_id=account_id,
                lang=lang
            )
            
            # Красивое форматирование с кликабельной почтой
            formatted_text = (
                "✅ <b>Временная почта создана!</b>\n\n"
                f"📧 <b>Email:</b> <code>{email_str}</code>\n\n"
                "💡 <i>Нажмите на адрес выше, чтобы скопировать его.</i>\n"
                "📝 Используйте /inbox для проверки входящих писем."
            )
            
            await message.answer(formatted_text, parse_mode="HTML")
                
        except Exception as e:
            logger.error(f"Error creating email for user {user_id}: {e}")
            await message.answer(t("error", lang))
        finally:
            await state.clear()


@router.message(Command("inbox"))
async def cmd_inbox(message: Message, lang: str = "ru"):
    """Обработчик команды /inbox"""
    user_id = get_user_id(message)
    logger.info(f"Пользователь {user_id} запросил просмотр писем")
    
    if not message.from_user:
        await message.answer(t("error_user", lang))
        return
    
    # Проверяем, есть ли активная почта
    user_data = get_user(message.from_user.id)
    if not user_data or not user_data.get('email'):
        await message.answer(t("no_mail", lang))
        return
    
    await message.answer(t("checking_inbox", lang))
    async with MailGwClient() as client:
        try:
            messages = await client.get_messages(user_data['token'])
            
            if not messages or len(messages) == 0:
                await message.answer(t("inbox_empty", lang, email=user_data['email']))
                return
            
            # Показываем список писем с inline кнопками
            await message.answer(
                t("inbox_messages", lang, email=user_data['email'], count=len(messages)),
                reply_markup=get_messages_keyboard(messages, lang)
            )
            
        except Exception as e:
            logger.error(f"Error fetching messages for user {user_id}: {e}")
            await message.answer(t("error_messages", lang))


@router.message(Command("delete"))
async def cmd_delete(message: Message, state: FSMContext, lang: str = "ru"):
    """Обработчик команды /delete"""
    user_id = get_user_id(message)
    logger.info(f"Пользователь {user_id} запросил удаление почты")
    
    if not message.from_user:
        await message.answer(t("error_user", lang))
        return
    
    # Проверяем, есть ли активная почта
    user_data = get_user(message.from_user.id)
    if not user_data or not user_data.get('email'):
        await message.answer(t("no_mail_delete", lang))
        return
    
    # Показываем подтверждение удаления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("delete_yes", lang), callback_data="confirm_delete_email"),
            InlineKeyboardButton(text=t("delete_no", lang), callback_data="cancel_delete_email")
        ]
    ])
    
    await message.answer(
        t("mail_delete_confirm", lang, email=user_data['email']),
        reply_markup=keyboard
    )
    await state.set_state(MailStates.confirm_deletion)


# Обработчики кнопок

@router.message(F.text.in_(["Получить почту", "Get email"]))
async def handle_get_mail(message: Message, state: FSMContext, lang: str = "ru"):
    """Обработчик кнопки 'Получить почту'"""
    await cmd_newmail(message, state, lang)


@router.message(F.text.in_(["Посмотреть письма", "View messages"]))
async def handle_view_mails(message: Message, lang: str = "ru"):
    """Обработчик кнопки 'Посмотреть письма'"""
    await cmd_inbox(message, lang)


@router.message(F.text.in_(["Удалить", "Delete"]))
async def handle_delete_mail(message: Message, state: FSMContext, lang: str = "ru"):
    """Обработчик кнопки 'Удалить'"""
    await cmd_delete(message, state, lang)


# Обработчики FSM callbacks

@router.callback_query(F.data == "confirm_new_email", MailStates.confirm_replacement)
async def callback_confirm_new_email(callback: CallbackQuery, state: FSMContext, lang: str = "ru"):
    """Подтверждение создания новой почты"""
    if not callback.message or not callback.from_user:
        await callback.answer(t("error", lang))
        return
    
    # Удаляем старую почту
    delete_user(callback.from_user.id)
    try:
        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(t("mail_creating", lang))
        else:
            await callback.answer(t("mail_creating", lang))
    except (TelegramBadRequest, AttributeError):
        await callback.answer(t("mail_creating", lang))
    
    async with MailGwClient() as client:
        try:
            # Генерируем email
            email_data = await client.generate_email()
            if not email_data:
                await callback.message.answer(t("error_connection", lang))
                await state.clear()
                return
            
            email_str = email_data["email"] if isinstance(email_data, dict) else email_data
            sid_token = email_data.get("sid_token", email_str) if isinstance(email_data, dict) else email_str
            
            password = generate_password()
            account_id = email_str
            
            # Сохраняем данные пользователя
            success = update_user(
                callback.from_user.id,
                email=email_str,
                password=password,
                token=sid_token,
                account_id=account_id,
                lang=lang
            )
            
            formatted_text = (
                "✅ <b>Временная почта создана!</b>\n\n"
                f"📧 <b>Email:</b> <code>{email_str}</code>\n\n"
                "💡 <i>Нажмите на адрес выше, чтобы скопировать его.</i>\n"
                "📝 Используйте /inbox для проверки входящих писем."
            )
            
            await callback.message.answer(formatted_text, parse_mode="HTML")
                
        except Exception as e:
            logger.error(f"Error creating email for user {callback.from_user.id}: {e}")
            await callback.message.answer(t("error", lang))
        finally:
            await state.clear()
    
    await callback.answer()


@router.callback_query(F.data == "cancel_new_email", MailStates.confirm_replacement)
async def callback_cancel_new_email(callback: CallbackQuery, state: FSMContext, lang: str = "ru"):
    """Отмена создания новой почты"""
    if not callback.message:
        await callback.answer(t("error", lang))
        return
    
    await state.clear()
    await callback.message.answer(t("operation_cancelled", lang))
    await callback.answer(t("operation_cancelled", lang))


@router.callback_query(F.data == "confirm_delete_email", MailStates.confirm_deletion)
async def callback_confirm_delete_email(callback: CallbackQuery, state: FSMContext, lang: str = "ru"):
    """Подтверждение удаления почты"""
    if not callback.message or not callback.from_user:
        await callback.answer(t("error", lang))
        return
    
    # Получаем данные пользователя
    user_data = get_user(callback.from_user.id)
    if not user_data or not user_data.get('email'):
        await callback.message.answer(t("no_mail_delete", lang))
        await state.clear()
        return
    
    async with MailGwClient() as client:
        try:
            success = await client.delete_account(
                user_data.get('account_id', ''), 
                user_data['token']
            )
            
            # Очищаем данные пользователя в любом случае
            delete_user(callback.from_user.id)
            
            if success:
                await callback.message.answer(t("mail_deleted", lang, email=user_data['email']))
            else:
                await callback.message.answer(t("error_delete", lang))
                
        except Exception as e:
            logger.error(f"Error deleting email for user {callback.from_user.id}: {e}")
            await callback.message.answer(t("error_delete", lang))
            delete_user(callback.from_user.id)
        finally:
            await state.clear()
    
    await callback.answer()


@router.callback_query(F.data == "cancel_delete_email", MailStates.confirm_deletion)
async def callback_cancel_delete_email(callback: CallbackQuery, state: FSMContext, lang: str = "ru"):
    """Отмена удаления почты"""
    if not callback.message:
        await callback.answer(t("error", lang))
        return
    
    await state.clear()
    await callback.message.answer(t("operation_cancelled_delete", lang))
    await callback.answer(t("operation_cancelled_delete", lang))


# Обработчики inline кнопок

@router.callback_query(F.data.startswith("view_message:"))
async def callback_view_message(callback: CallbackQuery, lang: str = "ru"):
    """Обработчик просмотра конкретного письма"""
    if not callback.from_user or not callback.data or not callback.message:
        await callback.answer(t("error_user", lang))
        return
    
    user_id = str(callback.from_user.id)
    message_id = callback.data.split(":", 1)[1]
    
    logger.info(f"Пользователь {user_id} запросил просмотр письма {message_id}")
    
    # Проверяем, есть ли активная почта
    user_data = get_user(callback.from_user.id)
    if not user_data or not user_data.get('email'):
        await callback.answer(t("no_mail", lang))
        return
    
    async with MailGwClient() as client:
        try:
            message_data = await client.get_message(message_id, user_data['token'])
            
            if not message_data:
                await callback.answer(t("error_messages", lang))
                return
            
            # Формируем текст письма
            subject = message_data.get('subject', 'Без темы')
            from_addr = message_data.get('from', 'Неизвестно')
            if isinstance(from_addr, dict):
                from_addr = from_addr.get('address', 'Неизвестно')
                
            created_at = message_data.get('date', message_data.get('createdAt', 'Неизвестно'))
            
            message_text = (
                f"📧 <b>Письмо</b>\n\n"
                f"<b>От:</b> {from_addr}\n"
                f"<b>Тема:</b> {subject}\n"
                f"<b>Дата:</b> {created_at}\n\n"
            )
            
            # Добавляем содержимое
            body = message_data.get('body', message_data.get('text', ''))
            if body:
                text_content = body[:1000]
                if len(body) > 1000:
                    text_content += "..."
                message_text += f"📄 <b>Содержимое:</b>\n<pre>{text_content}</pre>"
            elif 'intro' in message_data:
                intro = message_data['intro'][:500]
                if len(message_data['intro']) > 500:
                    intro += "..."
                message_text += f"📄 <b>Краткое содержание:</b>\n{intro}"
            else:
                message_text += "📄 <i>Текст письма недоступен</i>"
            
            await callback.message.answer(
                message_text,
                reply_markup=get_message_actions_keyboard(message_id, lang),
                parse_mode="HTML"
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error fetching message {message_id} for user {user_id}: {e}")
            await callback.answer(t("error_messages", lang))


@router.callback_query(F.data == "back_to_inbox")
async def callback_back_to_inbox(callback: CallbackQuery, lang: str = "ru"):
    """Обработчик возврата к списку писем"""
    if not callback.from_user or not callback.message:
        await callback.answer(t("error", lang))
        return
    
    user_id = str(callback.from_user.id)
    logger.info(f"Пользователь {user_id} вернулся к списку писем")
    
    # Проверяем, есть ли активная почта
    user_data = get_user(callback.from_user.id)
    if not user_data or not user_data.get('email'):
        await callback.answer(t("no_mail", lang))
        return
    
    async with MailGwClient() as client:
        try:
            messages = await client.get_messages(user_data['token'])
            
            if not messages or len(messages) == 0:
                inbox_text = t("inbox_empty", lang, email=user_data['email'])
                await callback.message.answer(inbox_text)
                return
            
            inbox_text = t("inbox_messages", lang, email=user_data['email'], count=len(messages))
            
            await callback.message.answer(
                inbox_text,
                reply_markup=get_messages_keyboard(messages, lang)
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error refreshing inbox for user {user_id}: {e}")
            await callback.answer(t("error_messages", lang))


@router.callback_query(F.data == "refresh_inbox")
async def callback_refresh_inbox(callback: CallbackQuery, lang: str = "ru"):
    """Обработчик обновления списка писем"""
    await callback_back_to_inbox(callback, lang)


@router.message(F.text & ~F.text.startswith('/'))
async def handle_unknown_message(message: Message, lang: str = "ru"):
    """Обработчик неизвестных текстовых сообщений (не команд)"""
    user_id = get_user_id(message)
    logger.info(f"Пользователь {user_id} отправил неизвестное сообщение: {message.text}")
    
    await message.answer(
        t("unknown_command", lang),
        reply_markup=get_main_keyboard(lang)
    )