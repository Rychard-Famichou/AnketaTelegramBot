import asyncio

from asgiref.sync import async_to_sync

from telegram_bot.bot import bot


async def send_telegram_notification_async(candidate, is_new: bool):
    """Асинхронная отправка стильного уведомления пользователю через Aiogram"""
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
        # В реальном проекте здесь лучше использовать logging.error
        print(f"Не удалось отправить уведомление в Telegram: {e}")


def send_telegram_notification(candidate, is_new: bool):
    """
    Фасад для безопасного запуска асинхронной отправки из синхронного контекста.
    Автоматически определяет наличие запущенного event loop.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(send_telegram_notification_async(candidate, is_new))
    except RuntimeError:
        # Если loop не запущен (например, в WSGI или тестах)
        async_to_sync(send_telegram_notification_async)(candidate, is_new)
