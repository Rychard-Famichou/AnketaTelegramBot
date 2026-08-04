import os

import django

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from django.conf import settings

# Оставляем инициализацию Django для корректного импорта моделей
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from candidates.handlers import router

# Инициализируем бота и диспетчер БЕЗ запуска пуллинга
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Заполнить анкету", web_app=WebAppInfo(url=settings.WEB_APP_URL))]],
        resize_keyboard=True,
    )
    await message.answer("Добро пожаловать! Откройте анкету:", reply_markup=kb)
