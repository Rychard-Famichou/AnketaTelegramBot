from unittest.mock import AsyncMock, patch

from django.core.management import call_command
from django.test import override_settings

import pytest

# Путь до объекта bot внутри файла вашей команды
COMMAND_BOT_PATH = "telegram_bot.management.commands.register_webhook.bot"


@override_settings(WEB_URL="https://testserver.com", TELEGRAM_SECRET_TOKEN="super_secret_test_token")
@pytest.mark.django_db
def test_register_webhook_command_success():
    """Тест успешной регистрации вебхука командой Django"""

    # Создаем мок для объекта bot
    mock_bot = AsyncMock()
    # AsyncMock автоматически делает свои под-атрибуты асинхронными моками,
    # но для надежности и явности сессии настроим их:
    mock_bot.set_webhook = AsyncMock()
    mock_bot.session.close = AsyncMock()

    # Патчим bot в модуле команды
    with patch(COMMAND_BOT_PATH, mock_bot):
        # Вызываем команду через официальный интерфейс Django (синхронно!)
        call_command("register_webhook")

        # 1. Проверяем, что set_webhook вызвался ровно 1 раз
        mock_bot.set_webhook.assert_called_once()

        # 2. Проверяем аргументы вызова метода set_webhook
        called_kwargs = mock_bot.set_webhook.call_args.kwargs
        assert called_kwargs["url"] == "https://testserver.com/webhook/secure-path/"
        assert called_kwargs["secret_token"] == "super_secret_test_token"
        assert called_kwargs["drop_pending_updates"] is True

        # 3. Проверяем, что сессия закрылась в блоке finally
        mock_bot.session.close.assert_called_once()


@override_settings(WEB_URL="https://testserver.com", TELEGRAM_SECRET_TOKEN="super_secret_test_token")
@pytest.mark.django_db
def test_register_webhook_command_exception_handling():
    """Тест того, что при ошибке Telegram API сессия бота все равно закроется"""

    mock_bot = AsyncMock()
    mock_bot.set_webhook = AsyncMock(side_effect=Exception("Telegram API Error"))
    mock_bot.session.close = AsyncMock()

    with patch(COMMAND_BOT_PATH, mock_bot):
        # Вызываем команду. Она внутренне перехватит ошибку в try-except
        # и выведет её в stdout, поэтому тест не упадет.
        call_command("register_webhook")

        # Проверяем, что даже при ошибке блок finally отработал и сессия закрыта
        mock_bot.set_webhook.assert_called_once()
        mock_bot.session.close.assert_called_once()
