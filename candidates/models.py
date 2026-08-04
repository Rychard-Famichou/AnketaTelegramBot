from django.db import models


# Create your models here.
class Candidate(models.Model):
    # Служебные данные Telegram
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=150, blank=True, null=True, verbose_name="Никнейм")

    # Данные из анкеты Web App
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    gender = models.CharField(max_length=20, verbose_name="Пол")
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подачи")

    class Meta:
        verbose_name = "Кандидат"
        verbose_name_plural = "Кандидаты"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} ({self.telegram_id})"
