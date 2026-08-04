import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from tg_bot import bot

class Command(BaseCommand):
    help = "Регистрация вебхука в Telegram (вызывается один раз перед стартом сервера)"

    def handle(self, *args, **options):
        webhook_url = f"{settings.WEB_URL}/webhook/secure-path/"

        async def main():
            try:
                self.stdout.write(f"Регистрация вебхука на URL: {webhook_url}...")
                await bot.set_webhook(
                    url=webhook_url,
                    secret_token=settings.TELEGRAM_SECRET_TOKEN,
                    drop_pending_updates=True
                )
                self.stdout.write(self.style.SUCCESS(" [Bot] Вебхук успешно зарегистрирован!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" [Bot] Ошибка: {e}"))
            finally:
                await bot.session.close()

        asyncio.run(main())
