import os

import django
from django.conf import settings

from aiogram import Bot, Dispatcher

# Инициализация Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Импорт роутера строго ПОСЛЕ django.setup()
from telegram_bot.handlers import router

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)
