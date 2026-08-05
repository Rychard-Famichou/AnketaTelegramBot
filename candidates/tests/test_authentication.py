import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from candidates.authentication import TelegramWebAppAuthentication, TelegramWebAppUser


# Вспомогательная функция для генерации валидной строки init_data и хеша
def generate_init_data(user_data, auth_date=None, bot_token="fake_bot_token"):
    if auth_date is None:
        auth_date = int(time.time())

    data = {
        "auth_date": str(auth_date),
        "user": json.dumps(user_data)
    }

    # Сортируем и собираем строку для подписи
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))

    # Считаем валидный HMAC-хеш
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    data["hash"] = expected_hash
    return urlencode(data)


@pytest.fixture(autouse=True)
def mock_telegram_token(settings):
    """Фикстура для установки тестового токена бота в настройки Django."""
    settings.TELEGRAM_BOT_TOKEN = "fake_bot_token"


@pytest.fixture
def factory():
    """Фикстура фабрики запросов DRF."""
    return APIRequestFactory()


@pytest.fixture
def valid_user_payload():
    """Фикстура с валидными данными пользователя Telegram."""
    return {
        "id": 123456,
        "first_name": "Ivan",
        "last_name": "Ivanov",
        "username": "vanya_test",
        "language_code": "ru"
    }


def test_auth_success(factory, valid_user_payload):
    """Проверка успешной аутентификации с валидными данными."""
    init_data = generate_init_data(valid_user_payload)
    request = factory.get("/", **{"HTTP_X_TELEGRAM_INIT_DATA": init_data})

    authenticator = TelegramWebAppAuthentication()
    user, auth_payload = authenticator.authenticate(request)

    # Проверка возвращаемого кортежа (User, Auth)
    assert isinstance(user, TelegramWebAppUser)
    assert user.is_authenticated is True
    assert user.id == valid_user_payload["id"]
    assert user.username == valid_user_payload["username"]
    assert auth_payload == valid_user_payload


def test_auth_no_header(factory):
    """Если заголовок отсутствует, метод должен вернуть None (пропустить к следующему бэкенду)."""
    request = factory.get("/")
    authenticator = TelegramWebAppAuthentication()

    result = authenticator.authenticate(request)
    assert result is None


def test_auth_corrupted_data(factory):
    """Проверка вызова исключения при битых или неполных данных."""
    # Передаем строку без обязательного поля hash
    init_data = "auth_date=12345&user={}"
    request = factory.get("/", **{"HTTP_X_TELEGRAM_INIT_DATA": init_data})

    authenticator = TelegramWebAppAuthentication()
    with pytest.raises(AuthenticationFailed, match="Некорректные данные Telegram."):
        authenticator.authenticate(request)


def test_auth_invalid_hash(factory, valid_user_payload):
    """Проверка вызова исключения, если хеш изменен (не совпадает подпись)."""
    init_data = generate_init_data(valid_user_payload)
    # Искажаем хеш, заменяя последний символ
    corrupted_init_data = init_data[:-1] + ("0" if init_data[-1] != "0" else "1")

    request = factory.get("/", **{"HTTP_X_TELEGRAM_INIT_DATA": corrupted_init_data})
    authenticator = TelegramWebAppAuthentication()

    with pytest.raises(AuthenticationFailed, match="Подпись Telegram не прошла проверку."):
        authenticator.authenticate(request)


def test_auth_expired_session(factory, valid_user_payload):
    """Проверка вызова исключения, если с момента auth_date прошло более 24 часов."""
    # Сессия устарела на 25 часов
    expired_time = int(time.time()) - (25 * 60 * 60)
    init_data = generate_init_data(valid_user_payload, auth_date=expired_time)

    request = factory.get("/", **{"HTTP_X_TELEGRAM_INIT_DATA": init_data})
    authenticator = TelegramWebAppAuthentication()

    with pytest.raises(AuthenticationFailed, match="Сессия Telegram устарела."):
        authenticator.authenticate(request)


def test_telegram_web_app_user_properties():
    """Тестирование инициализации самого объекта контейнера пользователя."""
    user_data = {"id": 999, "username": "ghost"}
    user = TelegramWebAppUser(user_data)

    assert user.id == 999
    assert user.username == "ghost"
    assert user.first_name is None  # Опциональное поле
    assert user.is_authenticated is True
