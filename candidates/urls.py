from django.urls import path

from candidates.views import AnketaFormView

urlpatterns = [
    # Страница будет доступна по URL: https://your-domain.com
    path('form/', AnketaFormView.as_view(), name='anketa_form'),
]
