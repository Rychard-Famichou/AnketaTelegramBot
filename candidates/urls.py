import os

from django.urls import path

from candidates.views import AnketaFormView, TelegramWebhookView, CandidateCreateAPIView, CandidateDetailAPIView

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "ВАШ_ТОКЕН_БОТА")

urlpatterns = [
    path('form/', AnketaFormView.as_view(), name='anketa_form'),
    path('api/candidates/', CandidateCreateAPIView.as_view(), name='candidate_create'),
    path('api/candidates/<int:telegram_id>/', CandidateDetailAPIView.as_view(), name='candidate_detail'),
    path(f'webhook/{BOT_TOKEN}/', TelegramWebhookView.as_view(), name='telegram_webhook'),
]
