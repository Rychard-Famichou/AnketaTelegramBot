FROM python:3.12-slim

# Настройки Python и Poetry 2.0 (пакеты ставятся глобально в систему)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.0.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

# Установка системных зависимостей для PostgreSQL и сборки пакетов
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Копируем конфигурационные файлы
COPY pyproject.toml README.md ./

# Генерируем чистый lock-файл прямо внутри Linux-контейнера и устанавливаем зависимости
RUN poetry lock && poetry install --no-root

# Копируем остальной код проекта
COPY . .

# Команда по умолчанию (будет переопределена в docker-compose)
CMD ["gunicorn", "config.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
