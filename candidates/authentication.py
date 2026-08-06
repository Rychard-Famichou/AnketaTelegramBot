import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class TelegramWebAppUser:
    """
    Анонимный объект-контейнер для хранения данных пользователя из Telegram.
    Используется, если в базе Django еще нет записи Candidate.
    """

    def __init__(self, user_data: dict):
        self.id = user_data.get("id")
        self.username = user_data.get("username")
        self.first_name = user_data.get("first_name")
        self.last_name = user_data.get("last_name")
        self.language_code = user_data.get("language_code")

    @property
    def is_authenticated(self):
        return True


class TelegramWebAppAuthentication(BaseAuthentication):
    """
    Кастомный класс аутентификации DRF для валидации данных Telegram WebApp.
    Проверяет заголовок X-Telegram-Init-Data.
    """

    def authenticate(self, request):
        init_data = request.headers.get("X-Telegram-Init-Data")

        # Если заголовка нет, DRF передает запрос следующему классу аутентификации
        if not init_data:
            return None

        try:
            # 1. Парсим строку инициализации
            data = dict(parse_qsl(init_data, keep_blank_values=True))
            received_hash = data.pop("hash")
            auth_date = int(data["auth_date"])
            user_data = json.loads(data["user"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise AuthenticationFailed("Некорректные данные Telegram.") from exc

        # 2. Проверяем валидность хеша (подписи)
        data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
        secret_key = hmac.new(
            b"WebAppData",
            settings.TELEGRAM_BOT_TOKEN.encode(),
            hashlib.sha256,
        ).digest()
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            raise AuthenticationFailed("Подпись Telegram не прошла проверку.")

        # 3. Проверяем устаревание сессии (24 часа)
        if time.time() - auth_date > 24 * 60 * 60:
            raise AuthenticationFailed("Сессия Telegram устарела.")

        return TelegramWebAppUser(user_data), user_data
