import asyncio
import json

from asgiref.sync import async_to_sync
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from candidates.forms import CandidateForm
from candidates.models import Candidate
from candidates.serializers import CandidateSerializer
from tg_bot import bot, dp
from aiogram.types import Update


# Create your views here.
class AnketaFormView(TemplateView):
    template_name = "anketa_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CandidateForm()  # Передаем пустую форму в шаблон
        return context


class CandidateCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        telegram_id = request.data.get("telegram_id")
        username = request.data.get("username")

        if not telegram_id:
            return Response({"error": "Telegram ID обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Используем стандартный синхронный метод get или создаем запись
        try:
            instance = Candidate.objects.get(telegram_id=telegram_id)
            is_new = False
        except Candidate.DoesNotExist:
            instance = None
            is_new = True

        # 2. Выполняем валидацию и сохранение стандартным синхронным методом DRF
        serializer = CandidateSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            candidate = serializer.save(telegram_id=telegram_id, username=username)

            # 3. Безопасно запускаем отправку сообщения в Telegram
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.send_telegram_notification(candidate, is_new))
            except RuntimeError:
                # На случай, если код запустился вне асинхронного контекста (например, в тестах)
                async_to_sync(self.send_telegram_notification)(candidate, is_new)

            return Response(serializer.data, status=status.HTTP_200_OK if not is_new else status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Метод отправки в бот ОСТАЕТСЯ асинхронным, так как aiogram требует await
    async def send_telegram_notification(self, candidate, is_new):
        """Асинправка стильного уведомления пользователю через Aiogram в фоне"""
        try:
            if is_new:
                text = (
                    "🎉 **Ваша анкета успешно создана!**\n\n"
                    f"📝 **Имя:** {candidate.first_name} {candidate.last_name}\n"
                    f"👤 **Пол:** {candidate.gender}\n"
                    f"📞 **Телефон:** {candidate.phone}\n\n"
                    "Спасибо за отклик! Менеджер свяжется с вами в ближайшее время."
                )
            else:
                text = (
                    "🔄 **Ваша анкета была успешно обновлена!**\n\n"
                    f"📝 **Новое имя:** {candidate.first_name} {candidate.last_name}\n"
                    f"👤 **Пол:** {candidate.gender}\n"
                    f"📞 **Телефон:** {candidate.phone}\n\n"
                    "Изменения успешно перезаписаны в базе данных."
                )

            await bot.send_message(chat_id=candidate.telegram_id, text=text, parse_mode="Markdown")
        except Exception as e:
            print(f"Не удалось отправить уведомление в Telegram: {e}")


class CandidateDetailAPIView(APIView):
    def get(self, request, telegram_id, *args, **kwargs):
        try:
            candidate = Candidate.objects.get(telegram_id=telegram_id)
            serializer = CandidateSerializer(candidate)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Candidate.DoesNotExist:
            return Response({"detail": "Кандидат не найден"}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    # Полностью асинный метод для ASGI
    async def post(self, request, *args, **kwargs):
        try:
            # Читаем тело запроса асинхронно (доступно в Django 4.0+)
            body = request.body.decode('utf-8')
            update_data = json.loads(body)

            update = Update(**update_data)

            # Нативно передаем в aiogram без оберток
            await dp.feed_update(bot, update)

            return HttpResponse("OK", status=200)
        except Exception as e:
            print(f"Ошибка в асинхронном вебхуке: {e}")
            return HttpResponse("Error", status=500)
