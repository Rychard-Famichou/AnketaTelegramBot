import pytest
from unittest.mock import AsyncMock
from aiogram import Bot

@pytest.fixture
def mock_bot(mocker):
    """Фикстура для подмены Telegram Bot API"""
    mock = mocker.MagicMock(spec=Bot)
    # Мокаем метод answer, который используется в вашем cmd_start
    mock.answer = AsyncMock()
    # Мокаем метод send_message (понадобится для уведомлений из DRF)
    mock.send_message = AsyncMock()
    return mock
