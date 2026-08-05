from unittest.mock import AsyncMock

from rest_framework.test import APIClient

import pytest
from aiogram.types import Chat, Message, User

from config import settings
from telegram_bot.handlers import check_status, cmd_start


@pytest.mark.asyncio
async def test_cmd_start_handler(mock_bot):
    # 1. Создаем фейковый объект сообщения
    chat = Chat(id=12345, type="private")
    user = User(id=12345, is_bot=False, first_name="Test")

    # Инициализируем сообщение, привязав наш замоканный бот
    message = Message(message_id=1, date=None, chat=chat, from_user=user, text="/start", bot=mock_bot)

    # 2. Вызываем хэндлер
    await cmd_start(message)

    # 3. Проверяем, что бот попытался ответить правильным текстом
    mock_bot.answer.assert_called_once()

    # Получаем аргументы, с которыми был вызван answer
    called_args, called_kwargs = mock_bot.answer.call_args

    assert "Добро пожаловать!" in called_args[0]
    assert called_kwargs["reply_markup"].keyboard[0][0].web_app.url == settings.WEB_APP_URL


@pytest.mark.asyncio
async def test_check_status_handler(mock_bot):
    # 1. Создаем фейковый объект сообщения
    chat = Chat(id=12345, type="private")
    user = User(id=12345, is_bot=False, first_name="Test")

    # Инициализируем сообщение, привязав наш замоканный бот
    message = Message(message_id=1, date=None, chat=chat, from_user=user, text="/start", bot=mock_bot)

    # 2. Вызываем хэндлер
    await check_status(message)
    # 3. Проверяем, что бот попытался ответить правильным текстом
    mock_bot.answer.assert_called_once()

    # Получаем аргументы, с которыми был вызван answer
    called_args, called_kwargs = mock_bot.answer.call_args

    assert "Вы еще не заполнили анкету. Нажмите на кнопку Web App ниже." in called_args[0]
    assert called_kwargs["reply_markup"].keyboard[0][0].web_app.url == settings.WEB_APP_URL


@pytest.mark.django_db
@pytest.mark.asyncio
def test_drf_view_sends_telegram_notification(mocker):
    # 1. Мокаем объект бота внутри вашего DRF-модуля, где вызывается отправка
    # Предположим, отправка идет через ваш инициализированный bot из файла main.py
    mock_send = mocker.patch("telegram_bot.main.bot.send_message", new_callable=AsyncMock)

    # 2. Делаем запрос к API
    client = APIClient()
    response = client.post("/api/v1/orders/", {"item": "Книга", "price": 500})

    # 3. Проверки
    assert response.status_code == 201

    # Проверяем, ушло ли уведомление в Телеграм
    mock_send.assert_called_once()
    kwargs = mock_send.call_args[1]
    assert "Новый заказ" in kwargs["text"]
    assert kwargs["chat_id"] == 12345  # ID админа или пользователя
