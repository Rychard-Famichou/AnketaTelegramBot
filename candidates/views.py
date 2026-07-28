from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class AnketaFormView(TemplateView):
    # Указываем путь к HTML-шаблону внутри вашей папки templates
    template_name = "anketa_form.html"
    