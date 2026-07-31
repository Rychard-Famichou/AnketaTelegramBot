from aiogram import Router, F
from aiogram.types import Message

from candidates.models import Candidate

router = Router()


@router.message(F.text == "/status")
async def check_status(message: Message):
    user_id = message.from_user.id

    try:
        candidate = await Candidate.objects.aget(telegram_id=user_id)
        await message.answer(
            f"Вы уже подали анкету! Статус: зарегистрирован. Дата: {candidate.created_at.strftime('%d.%m.%Y')}")
    except Candidate.DoesNotExist:
        await message.answer("Вы еще не заполнили анкету. Нажмите на кнопку Web App ниже.")
