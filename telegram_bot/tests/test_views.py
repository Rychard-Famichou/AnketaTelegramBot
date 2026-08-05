from unittest.mock import AsyncMock, patch

from django.urls import reverse

import pytest

# Константы для тестов
SECRET_TOKEN = "super_secret_token_123"
URL = reverse("telegram_webhook")


@pytest.fixture(autouse=True)
def mock_telegram_settings(settings):
    """Фикстура для установки секретного токена в настройки Django."""
    settings.TELEGRAM_SECRET_TOKEN = SECRET_TOKEN


@pytest.fixture
def mock_feed_update():
    """Фикстура для мокания метода feed_update у aiogram dispatcher."""
    with patch("telegram_bot.bot.dp.feed_update", new_callable=AsyncMock) as mock:
        yield mock


@pytest.mark.django_db
@pytest.mark.asyncio
class TestTelegramWebhookView:

    async def test_invalid_secret_token_returns_403(self, async_client, mock_feed_update):
        """1. Неверный токен возвращает 403, и обработчик aiogram не вызывается."""
        headers = {"HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN": "wrong_token"}
        payload = {
            "update_id": 12345,
            "message": {
                "message_id": 1,
                "date": 0,
                "chat": {"id": 111, "type": "private"},
                "from": {"id": 111, "is_bot": False, "first_name": "Test"},
                "text": "Hi"
            }
        }

        response = await async_client.post(URL, data=payload, content_type="application/json", **headers)

        assert response.status_code == 403
        assert "неверный секретный токен" in response.content.decode("utf-8")
        mock_feed_update.assert_not_called()

    async def test_valid_token_and_update_returns_200(self, async_client, mock_feed_update):
        """2. Корректный токен и update возвращают 200, вызывается feed_update."""
        headers = {"HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN": SECRET_TOKEN}
        payload = {
            "update_id": 12345,
            "message": {
                "message_id": 1,
                "date": 0,
                "chat": {"id": 111, "type": "private"},
                "from": {"id": 111, "is_bot": False, "first_name": "Test"},
                "text": "Hi"
            }
        }

        response = await async_client.post(URL, data=payload, content_type="application/json", **headers)

        assert response.status_code == 200
        assert response.content.decode("utf-8") == "OK"

        # Проверяем, что метод feed_update был вызван ровно 1 раз
        mock_feed_update.assert_called_once()

        # Проверяем, что в метод передали объект Update с правильным id
        called_args, called_kwargs = mock_feed_update.call_args
        passed_update = called_args[1]  # Второй позиционный аргумент (после bot)
        assert passed_update.update_id == 12345

    async def test_invalid_json_returns_400(self, async_client, mock_feed_update):
        """3. Некорректный JSON/update возвращает 400, и обработчик не вызывается."""
        headers = {"HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN": SECRET_TOKEN}
        invalid_payload = '{"invalid_field": "no_update_id_here"}'

        response = await async_client.post(URL, data=invalid_payload, content_type="application/json", **headers)

        assert response.status_code == 400
        assert "Некорректный формат Update." in response.content.decode("utf-8")
        mock_feed_update.assert_not_called()
