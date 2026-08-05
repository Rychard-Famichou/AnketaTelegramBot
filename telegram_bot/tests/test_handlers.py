from datetime import datetime
from unittest.mock import AsyncMock

from django.conf import settings

import pytest
from aiogram.types import Chat, Message, User

from candidates.models import Candidate
from telegram_bot.handlers import check_status, cmd_start


@pytest.mark.asyncio
async def test_cmd_start_handler():
    # 1. Готовим валидные данные
    chat = Chat(id=12345, type="private")
    user = User(id=12345, is_bot=False, first_name="Test")
    message = Message(message_id=1, date=datetime.now(), chat=chat, from_user=user, text="/start")

    message.answer = AsyncMock()

    # 2. Вызываем хэндлер
    await cmd_start(message)

    # 3. Проверяем вызовы
    message.answer.assert_called_once()
    called_args, called_kwargs = message.answer.call_args

    # Проверяем текст ответа
    assert "Добро пожаловать!" in called_args[0]

    web_app_url = called_kwargs["reply_markup"].keyboard[0][0].web_app.url
    assert web_app_url == settings.WEB_APP_URL


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_check_status_handler_candidate_not_exists():
    """Тест случая, когда кандидата нет в базе данных (DoesNotExist)"""
    chat = Chat(id=12345, type="private")
    user = User(id=11111, is_bot=False, first_name="NewUser")
    message = Message(message_id=2, date=datetime.now(), chat=chat, from_user=user, text="/status")
    message.answer = AsyncMock()

    # Вызываем хэндлер
    await check_status(message)

    # Проверяем текст для ветки Должно выдать: 'Вы еще не заполнили анкету...'
    message.answer.assert_called_once()
    called_args, _ = message.answer.call_args
    assert "Вы еще не заполнили анкету" in called_args[0]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_check_status_handler_candidate_exists():
    """Тест случая, когда кандидат успешно найден в базе данных"""
    # 1. Создаем тестовую запись в БД Django. Используем асинхронный acreate.
    telegram_id = 99999
    await Candidate.objects.acreate(
        telegram_id=telegram_id,
        first_name="Ivan",
        last_name="Ivanov",
        gender="male",
        phone="+79991112233",
    )

    chat = Chat(id=12345, type="private")
    user = User(id=telegram_id, is_bot=False, first_name="ExistingUser")
    message = Message(message_id=3, date=datetime.now(), chat=chat, from_user=user, text="/status")
    message.answer = AsyncMock()

    # 2. Вызываем хэндлер
    await check_status(message)

    # 3. Проверяем, что хэндлер зашел в ветку try: и выдал статус
    message.answer.assert_called_once()
    called_args, _ = message.answer.call_args
    assert "Вы уже подали анкету! Статус: зарегистрирован." in called_args[0]
