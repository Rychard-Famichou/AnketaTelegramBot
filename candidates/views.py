from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from candidates.authentication import TelegramWebAppAuthentication
from candidates.forms import CandidateForm
from candidates.models import Candidate
from candidates.serializers import CandidateSerializer
from telegram_bot.services import send_telegram_notification


# Create your views here.
class AnketaFormView(TemplateView):
    template_name = "anketa_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CandidateForm()
        return context


class CandidateCreateAPIView(APIView):
    authentication_classes = [TelegramWebAppAuthentication]

    def post(self, request, *args, **kwargs):
        telegram_id = request.user.id
        username = request.user.username

        instance = Candidate.objects.filter(telegram_id=telegram_id).first()
        is_new = instance is None

        serializer = CandidateSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            candidate = serializer.save(
                telegram_id=telegram_id,
                username=username,
            )
            send_telegram_notification(candidate, is_new)
            return Response(serializer.data, status=status.HTTP_200_OK if not is_new else status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CandidateDetailAPIView(APIView):
    authentication_classes = [TelegramWebAppAuthentication]

    def get(self, request, *args, **kwargs):
        try:
            candidate = Candidate.objects.get(telegram_id=request.user.id)
        except Candidate.DoesNotExist:
            return Response(
                {"detail": "Кандидат не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(CandidateSerializer(candidate).data)
