"""
API клиент для работы с Guerrilla Mail API
"""

import asyncio
import logging
import random
import string
import time
from typing import Dict, List, Optional, Any
import aiohttp

logger = logging.getLogger(__name__)

BASE_URL = "https://api.guerrillamail.com/ajax.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


class MailGwClient:
    """Клиент для работы с Guerrilla Mail API (адаптированный под ваш интерфейс)"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = {}
        self.cache_ttl = 60
        
    async def __aenter__(self):
        await self.start_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
        
    async def start_session(self):
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=15)
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=HEADERS,
                connector=connector
            )
            
    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
            
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        _, timestamp = self.cache[key]
        return time.time() - timestamp < self.cache_ttl
        
    def _get_from_cache(self, key: str) -> Optional[Any]:
        if self._is_cache_valid(key):
            data, _ = self.cache[key]
            return data
        return None
        
    def _set_cache(self, key: str, data: Any):
        self.cache[key] = (data, time.time())
        
    async def _make_request(self, params: Dict[str, Any]) -> Optional[Any]:
        await self.start_session()
        
        if not self.session:
            logger.error("HTTP session is not available")
            return None
            
        try:
            logger.info(f"Making GET request to Guerrilla Mail with params: {params}")
            async with self.session.get(BASE_URL, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Guerrilla Mail request failed with status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error requesting Guerrilla Mail: {e}")
            return None

    def generate_username(self, length: int = 8) -> str:
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for _ in range(length))

    async def generate_email(self) -> Optional[Dict[str, str]]:
        """Создает почтовый ящик в Guerrilla Mail"""
        logger.info("Generating new email address via Guerrilla Mail")
        
        # Запрашиваем новый почтовый ящик
        params = {"f": "get_email_address"}
        result = await self._make_request(params)
        
        if result and "email_addr" in result:
            email = result["email_addr"]
            sid_token = result.get("sid_token", "")
            alias = result.get("alias", "")
            
            logger.info(f"Generated email: {email}")
            return {
                "email": email,
                "login": alias or email.split("@")[0],
                "domain": email.split("@")[1] if "@" in email else "guerrillamail.com",
                "sid_token": sid_token
            }
            
        logger.error(f"Failed to generate email from Guerrilla Mail. Response: {result}")
        return None

    async def get_domains(self) -> Optional[List[str]]:
        """Возвращает стандартные домены Guerrilla Mail"""
        return ["guerrillamail.com", "guerrillamail.net", "sharklasers.com", "grr.la"]

    async def create_account(self, email: str, password: Optional[str] = None) -> Optional[Dict[str, str]]:
        return {
            "id": email,
            "address": email
        }

    async def get_token(self, email: str, password: Optional[str] = None) -> Optional[str]:
        return email

    async def get_messages(self, token_or_email: str) -> List[Dict[str, Any]]:
        """
        Получает список входящих писем для сессии.
        В качестве sid_token можно использовать токен сессии Guerrilla Mail.
        """
        params = {
            "f": "get_email_list",
            "offset": 0
        }
        
        # Если передан sid_token
        if token_or_email and not "@" in token_or_email:
            params["sid_token"] = token_or_email

        result = await self._make_request(params)
        
        if result and "list" in result:
            raw_list = result["list"]
            # Адаптируем ответ под привычный формат писем
            formatted_messages = []
            for item in raw_list:
                formatted_messages.append({
                    "id": item.get("mail_id"),
                    "from": item.get("mail_from"),
                    "subject": item.get("mail_subject"),
                    "date": item.get("mail_date")
                })
            return formatted_messages
            
        return []

    async def get_message(self, message_id: int, token_or_email: str) -> Optional[Dict[str, Any]]:
        """Получение текста и деталей конкретного письма по его ID"""
        cache_key = f"message_{message_id}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
            
        params = {
            "f": "fetch_email",
            "email_id": message_id
        }
        
        if token_or_email and not "@" in token_or_email:
            params["sid_token"] = token_or_email

        result = await self._make_request(params)
        if result and "mail_body" in result:
            formatted_message = {
                "id": result.get("mail_id"),
                "from": result.get("mail_from"),
                "subject": result.get("mail_subject"),
                "date": result.get("mail_date"),
                "body": result.get("mail_body"),
                "html": result.get("mail_body")
            }
            self._set_cache(cache_key, formatted_message)
            return formatted_message
            
        return None

    async def delete_account(self, account_id: str, token: Optional[str] = None) -> bool:
        logger.info(f"Guerrilla Mail session cleared for {account_id}")
        return True