from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from aiogram.types import Chat, Message, User

from candidates.models import Candidate
from telegram_bot.handlers import check_status, cmd_start


@pytest.mark.asyncio
async def test_cmd_start_handler(mocker):
    # 1. Готовим валидные данные
    chat = Chat(id=12345, type="private")
    user = User(id=12345, is_bot=False, first_name="Test")
    message = Message(message_id=1, date=datetime.now(), chat=chat, from_user=user, text="/start")

    mock_answer = mocker.patch.object(message, "answer", new_callable=AsyncMock)

    # 2. Вызываем хэндлер
    await cmd_start(message)

    # 3. Проверяем вызовы
    mock_answer.assert_called_once_with("Добро пожаловать!")


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_check_status_handler_candidate_not_exists(mocker):
    """Тест случая, когда кандидата нет в базе данных (DoesNotExist)"""
    chat = Chat(id=12345, type="private")
    user = User(id=11111, is_bot=False, first_name="NewUser")
    message = Message(message_id=2, date=datetime.now(), chat=chat, from_user=user, text="/status")

    # Мокаем метод answer
    mock_answer = mocker.patch.object(message, "answer", new_callable=AsyncMock)

    # Вызываем хэндлер
    await check_status(message)

    # Одной этой строчки достаточно: она проверяет и факт вызова, и точный текст
    mock_answer.assert_called_once_with("Вы еще не заполнили анкету. Нажмите на кнопку Web App ниже.")


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_check_status_handler_candidate_exists(mocker):
    """Тест случая, когда кандидат успешно найден в базе данных"""
    telegram_id = 99999

    # 1. Создаем тестовую запись в БД Django.
    candidate = await Candidate.objects.acreate(
        telegram_id=telegram_id,
        first_name="Ivan",
        last_name="Ivanov",
        gender="male",
        phone="+79991112233",
    )

    # Получаем отформатированную дату, которую сгенерировала БД (или Django)
    expected_date_str = candidate.created_at.strftime("%d.%m.%Y")

    chat = Chat(id=12345, type="private")
    user = User(id=telegram_id, is_bot=False, first_name="ExistingUser")
    message = Message(message_id=3, date=datetime.now(), chat=chat, from_user=user, text="/status")

    # Мокаем метод answer
    mock_answer = mocker.patch.object(message, "answer", new_callable=AsyncMock)

    # 2. Вызываем хэндлер
    await check_status(message)

    # 3. Проверяем строгий текст с учетом правильного формата даты
    mock_answer.assert_called_once_with(f"Вы уже подали анкету! Статус: зарегистрирован. Дата: {expected_date_str}")
