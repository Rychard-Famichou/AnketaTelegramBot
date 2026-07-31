from django.conf import settings
from django.core.management.base import BaseCommand

import psycopg
from psycopg import sql


class Command(BaseCommand):
    help = "Создает базу данных PostgreSQL, если она еще не существует"

    def handle(self, *args, **options):
        db_settings = settings.DATABASES.get("default", {})

        target_db = db_settings.get("NAME")
        db_user = db_settings.get("USER")
        db_password = db_settings.get("PASSWORD")
        db_host = db_settings.get("HOST")
        db_port = db_settings.get("PORT")

        self.stdout.write(f"Подключение к PostgreSQL для создания базы '{target_db}'...")

        try:
            with psycopg.connect(
                dbname="postgres", user=db_user, password=db_password, host=db_host, port=db_port, autocommit=True
            ) as conn:

                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
                    exists = cur.fetchone()

                    if not exists:
                        cur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(target_db)))
                        self.stdout.write(self.style.SUCCESS(f"База данных '{target_db}' успешно создана!"))
                    else:
                        self.stdout.write(f"База данных '{target_db}' уже существует.")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Не удалось создать базу данных. Ошибка: {e}"))
