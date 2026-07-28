import os
import django
import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# 1. Настройка окружения Django (Важно сделать ДО импорта моделей!)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project.settings")
django.setup()

# Теперь мы можем безопасно импортировать модели
from candidates.models import Candidate

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(
            text="Заполнить анкету",
            web_app=WebAppInfo(url=os.getenv("WEB_APP_URL"))
        )]],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать! Заполните анкету:", reply_markup=kb)


@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    data = json.loads(message.web_app_data.data)

    # Спокойно используем асинхронный метод Django ORM
    await Candidate.objects.acreate(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data['name'],
        specialty=data['specialty'],
        experience=data['experience']
    )
    await message.answer("Спасибо! Ваша анкета сохранена.")


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
