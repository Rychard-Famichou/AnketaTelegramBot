from unittest.mock import AsyncMock, patch

from django.core.management import call_command
from django.test import override_settings

import pytest


# Задаем фейковые настройки для изоляции теста
@override_settings(WEB_URL="https://testserver.com", TELEGRAM_SECRET_TOKEN="super_secret_test_token")
@pytest.mark.django_db
@pytest.mark.asyncio
async def test_register_webhook_command_success():
    """Тест успешной регистрации вебхука командой Django"""

    # Пути для моканья методов бота (укажите ваш путь импорта bot)
    bot_path = "bot.bot"

    # Создаем асинхронные моки для методов сессии и вебхука
    mock_register_webhook = AsyncMock()
    mock_close_session = AsyncMock()

    # Патчим методы объекта bot напрямую
    with (
        patch(f"{bot_path}.register_webhook", mock_register_webhook),
        patch(f"{bot_path}.session.close", mock_close_session),
    ):
        await call_command("register_webhook")

        # 1. Проверяем, что register_webhook вызвался ровно 1 раз
        mock_register_webhook.assert_called_once()

        # 2. Проверяем аргументы вызова
        called_kwargs = mock_register_webhook.call_args.kwargs
        assert called_kwargs["url"] == "https://testserver.com"
        assert called_kwargs["secret_token"] == "super_secret_test_token"
        assert called_kwargs["drop_pending_updates"] is True

        # 3. Проверяем, что сессия закрылась в блоке finally
        mock_close_session.assert_called_once()


@override_settings(WEB_URL="https://testserver.com", TELEGRAM_SECRET_TOKEN="super_secret_test_token")
@pytest.mark.django_db
@pytest.mark.asyncio
async def test_register_webhook_command_exception_handling():
    """Тест того, что при ошибке Telegram API сессия бота все равно закроется"""

    bot_path = "bot.bot"

    # Мокаем register_webhook так, чтобы он выбрасывал ошибку
    mock_register_webhook = AsyncMock(side_effect=Exception("Telegram API Error"))
    mock_close_session = AsyncMock()

    with (
        patch(f"{bot_path}.register_webhook", mock_register_webhook),
        patch(f"{bot_path}.session.close", mock_close_session),
    ):
        # Команда перехватывает ошибку внутри себя (try/except), поэтому тест не упадет
        await call_command("register_webhook")

        # Проверяем, что даже при ошибке блок finally отработал и сессия закрыта
        mock_register_webhook.assert_called_once()
        mock_close_session.assert_called_once()
