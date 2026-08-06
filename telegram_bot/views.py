from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from aiogram.types import Update
from pydantic import ValidationError

from telegram_bot.bot import bot, dp


# Create your views here.
@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    # Полностью асинный метод для ASGI
    async def post(self, request, *args, **kwargs):
        received_token = request.META.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN")
        if received_token != settings.TELEGRAM_SECRET_TOKEN:
            return HttpResponseForbidden("Доступ запрещен: неверный секретный токен.")
        try:
            # Превращаем сырой текст запроса в объект Update
            update = Update.model_validate_json(request.body.decode("utf-8"))
            # Нативно передаем в aiogram без оберток
            await dp.feed_update(bot, update)
            return HttpResponse("OK", status=200)

        except ValidationError:
            # Перехватываем ошибку валидации Pydantic для некорректного JSON
            return HttpResponseBadRequest("Некорректный формат Update.")

        except Exception as e:
            print(f"Ошибка в асинхронном вебхуке: {e}")
            return HttpResponse("Error", status=500)
