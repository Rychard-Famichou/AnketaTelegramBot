from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo
from django.conf import settings

from candidates.models import Candidate

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Заполнить анкету",
                    web_app=WebAppInfo(url=settings.WEB_APP_URL),
                )
            ]
        ],
        resize_keyboard=True,
    )
    await message.answer("Добро пожаловать! Откройте анкету:", reply_markup=kb)


@router.message(F.text == "/status")
async def check_status(message: Message):
    user_id = message.from_user.id

    try:
        candidate = await Candidate.objects.aget(telegram_id=user_id)
        await message.answer(
            f"Вы уже подали анкету! Статус: зарегистрирован. Дата: {candidate.created_at.strftime('%d.%m.%Y')}"
        )
    except Candidate.DoesNotExist:
        await message.answer(
            "Вы еще не заполнили анкету. Нажмите на кнопку Web App ниже."
        )
