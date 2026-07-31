from django import forms
from .models import Candidate


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        # Указываем только те поля, которые пользователь должен заполнить вручную
        fields = ['first_name', 'last_name', 'gender', 'phone']

        # Автоматически добавляем виджеты (опционально, для стилизации)
        widgets = {
            'gender': forms.Select(choices=[('Мужской', 'Мужской'), ('Женский', 'Женский')]),
        }
