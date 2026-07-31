import os
import django
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from asgiref.sync import sync_to_async


# Оставляем инициализацию Django для корректного импорта моделей
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
if not apps.ready if 'apps' in locals() else True:
    django.setup()

from candidates.models import Candidate

# Инициализируем бота и диспетчер БЕЗ запуска пуллинга
bot = Bot(token=os.getenv("TELEGRAM_TOKEN", "ВАШ_ТОКЕН_БОТА"))
dp = Dispatcher()


# Функция сохранения в БД
def save_candidate(user_id, username, name, spec, exp):
    return Candidate.objects.create(
        telegram_id=user_id, username=username, full_name=name, specialty=spec, experience=exp
    )


async_save_candidate = sync_to_async(save_candidate, thread_sensitive=True)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Заполнить анкету", web_app=WebAppInfo(url=os.getenv("WEB_APP_URL")))]],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать! Откройте анкету:", reply_markup=kb)


# Хэндлер данных из Web App
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    print("\n!!! ВЕБХУК УСПЕШНО ПРИНЯЛ ДАННЫЕ АНКЕТЫ !!!")
    print(f"Данные: {message.web_app_data.data}")

    try:
        data = json.loads(message.web_app_data.data)
        await async_save_candidate(
            user_id=message.from_user.id,
            username=message.from_user.username,
            name=data.get('name'),
            spec=data.get('specialty'),
            exp=data.get('experience')
        )
        await message.answer("Отлично! Ваша анкета сохранена в PostgreSQL.")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
