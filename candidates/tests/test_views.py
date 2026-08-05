import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from candidates.models import Candidate
from candidates.authentication import TelegramWebAppUser


@pytest.fixture
def api_client():
    """Фикстура для DRF APIClient."""
    return APIClient()


@pytest.fixture
def mock_tg_user():
    """Фикстура, имитирующая авторизованного пользователя Telegram."""
    return TelegramWebAppUser({
        "id": 123456789,
        "username": "test_tg_user",
        "first_name": "Ivan"
    })


@pytest.fixture
def mock_authenticate(mock_tg_user):
    """Патч для обхода проверки подписи в тестах эндпоинтов.

    Имитирует успешную аутентификацию, возвращая нашего mock_tg_user.
    """
    with patch("candidates.authentication.TelegramWebAppAuthentication.authenticate") as mock_auth:
        mock_auth.return_value = (mock_tg_user, {})
        yield mock_auth


@pytest.mark.django_db
class TestCandidateAPI:

    @patch("candidates.views.send_telegram_notification")
    def test_create_candidate_success(self, mock_notify, api_client, mock_authenticate, mock_tg_user):
        """Тест успешного создания нового кандидата."""
        url = reverse("candidate_create")
        payload = {
            "first_name": "Иван",
            "last_name": "Иванов",
            "phone": "+79991112233"
        }

        # Передаем заголовок, чтобы сработал наш пропатченный метод authenticate
        response = api_client.post(url, data=payload, format="json", HTTP_X_TELEGRAM_INIT_DATA="valid_str")

        assert response.status_code == status.HTTP_201_CREATED
        assert Candidate.objects.filter(telegram_id=mock_tg_user.id).exists()

        # Проверяем, что функция уведомлений была вызвана с флагом is_new=True
        candidate = Candidate.objects.get(telegram_id=mock_tg_user.id)
        mock_notify.assert_called_once_with(candidate, True)

    @patch("candidates.views.send_telegram_notification")
    def test_update_candidate_success(self, mock_notify, api_client, mock_authenticate, mock_tg_user):
        """Тест успешного обновления существующего кандидата (partial update)."""
        # Сначала создаем кандидата в БД
        existing_candidate = Candidate.objects.create(
            telegram_id=mock_tg_user.id,
            username=mock_tg_user.username,
            first_name="СтароеИмя"
        )

        url = reverse("candidate_create")
        payload = {"first_name": "НовоеИмя"}

        response = api_client.post(url, data=payload, format="json", HTTP_X_TELEGRAM_INIT_DATA="valid_str")

        assert response.status_code == status.HTTP_200_OK
        existing_candidate.refresh_from_db()
        assert existing_candidate.first_name == "НовоеИмя"

        # Проверяем, что функция уведомлений вызвана с флагом is_new=False
        mock_notify.assert_called_once_with(existing_candidate, False)

    def test_create_candidate_invalid_data(self, api_client, mock_authenticate):
        """Тест отправки некорректных данных (ошибка валидации сериализатора)."""
        url = reverse("candidate_create")
        # Предположим, что поля валидируются и пустой словарь вызовет ошибку
        payload = {"phone": "не-телефон"}

        response = api_client.post(url, data=payload, format="json", HTTP_X_TELEGRAM_INIT_DATA="valid_str")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data

    def test_get_candidate_detail_success(self, api_client, mock_authenticate, mock_tg_user):
        """Тест успешного получения данных профиля."""
        Candidate.objects.create(
            telegram_id=mock_tg_user.id,
            username=mock_tg_user.username,
            first_name="Иван"
        )

        url = reverse("candidate_detail")
        response = api_client.get(url, HTTP_X_TELEGRAM_INIT_DATA="valid_str")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["telegram_id"] == mock_tg_user.id
        assert response.data["first_name"] == "Иван"

    def test_get_candidate_detail_not_found(self, api_client, mock_authenticate):
        """Тест получения профиля, если записи в базе еще нет."""
        url = reverse("candidate_detail")
        response = api_client.get(url, HTTP_X_TELEGRAM_INIT_DATA="valid_str")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Кандидат не найден"

    def test_api_unauthorized(self, api_client):
        """Проверка, что без заголовка аутентификации доступ запрещен (IsAuthenticated)."""
        url = reverse("candidate_detail")
        response = api_client.get(url)  # Не передаем заголовок

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("candidates.views.send_telegram_notification")
    def test_json_payload_cannot_override_telegram_id_and_username(self, mock_notify, api_client, mock_authenticate,
                                                                   mock_tg_user):
        """
        Проверка: Telegram ID и username, присланные злоумышленником в JSON-теле,
        НЕ МОГУТ подменить доверенные данные, полученные из initData.
        """
        url = reverse("candidate-create-url-name")

        # Злоумышленник (mock_tg_user) пытается в JSON передать чужие id и username
        malicious_payload = {
            "telegram_id": 999999999,  # Чужой ID
            "username": "hacker_username",  # Чужой username
            "first_name": "Взломщик",
            "last_name": "Петров"
        }

        # Делаем запрос от лица mock_tg_user (у него ID = 123456789, username = test_tg_user)
        response = api_client.post(url, data=malicious_payload, format="json", HTTP_X_TELEGRAM_INIT_DATA="valid_str")

        assert response.status_code == status.HTTP_201_CREATED

        # Проверяем базу данных: запись должна создаться ТОЛЬКО для нашего легитимного mock_tg_user
        candidate = Candidate.objects.get(first_name="Взломщик")

        assert candidate.telegram_id == mock_tg_user.id  # Сохранился ID из initData, а не из JSON
        assert candidate.username == mock_tg_user.username  # Сохранился username из initData, а не из JSON
        assert not Candidate.objects.filter(telegram_id=999999999).exists()  # Чужой ID в базу не попал

    def test_user_a_cannot_get_or_update_user_b_data(self, api_client):
        """
        Проверка: Пользователь А не может получить или обновить анкету пользователя Б.
        """
        # 1. Создаем в базе данных анкету Пользователя Б (жертва)
        user_b_id = 888888888
        candidate_b = Candidate.objects.create(
            telegram_id=user_b_id,
            username="user_b",
            first_name="Борис"
        )

        # 2. Имитируем вход Пользователя А (злоумышленник)
        user_a = TelegramWebAppUser({
            "id": 111111111,
            "username": "user_a"
        })

        # Нам нужно динамически подменить аутентификацию именно на Пользователя А
        with patch("candidates.authentication.TelegramWebAppAuthentication.authenticate") as mock_auth:
            mock_auth.return_value = (user_a, {})

            # --- ПРОВЕРКА ЧТЕНИЯ (GET) ---
            # Пользователь А запрашивает детали (внутри view берётся id из request.user.id)
            url_detail = reverse("candidate_detail")
            response_get = api_client.get(url_detail, HTTP_X_TELEGRAM_INIT_DATA="valid_str")

            # Должен вернуться 404, так как у Пользователя А ещё нет анкеты в базе
            assert response_get.status_code == status.HTTP_404_NOT_FOUND
            assert response_get.data["detail"] == "Кандидат не найден"

            # --- ПРОВЕРКА ОБНОВЛЕНИЯ (POST) ---
            # Пользователь А пытается отправить форму, надеясь перезаписать данные Бориса.
            # Если бы мы искали кандидата по id из JSON, это бы сработало. Но ваше View ищет по request.user.id.
            url_create = reverse("candidate_create")
            payload = {"first_name": "ПопыткаВзлома"}

            with patch("candidates.views.send_telegram_notification"):  # Изолируем отправку ТГ
                response_post = api_client.post(url_create, data=payload, format="json",
                                                HTTP_X_TELEGRAM_INIT_DATA="valid_str")

            # Так как у Пользователя А анкеты не было, создастся НОВАЯ анкета для Пользователя А (201)
            assert response_post.status_code == status.HTTP_201_CREATED

            # Проверяем, что анкета Бориса (Пользователя Б) осталась нетронутой
            candidate_b.refresh_from_db()
            assert candidate_b.first_name == "Борис"  # Имя не изменилось на "ПопыткаВзлома"

            # Проверяем, что изменения применились к новой анкете Пользователя А
            candidate_a = Candidate.objects.get(telegram_id=user_a.id)
            assert candidate_a.first_name == "ПопыткаВзлома"


def test_anketa_form_view(client):
    """Тест стандартного Django TemplateView на корректность контекста и формы."""
    url = reverse("anketa_form")
    response = client.get(url)

    assert response.status_code == 200
    assert "form" in response.context
    assert "anketa_form.html" in [t.name for t in response.templates]
