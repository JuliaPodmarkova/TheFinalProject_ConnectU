# Stage 1: Builder (остаётся как есть)
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
 && rm -rf /var/lib/apt/lists/*
 
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# --------------------------------------------------------------------

# Stage 2: Final stage (вносим изменения сюда)
FROM python:3.10-slim

# ВОТ РЕШЕНИЕ: Устанавливаем psql здесь, где он действительно нужен
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache /wheels/*
# Копируем наш скрипт ожидания ВНУТРЬ образа
COPY wait-for-it.sh .

COPY . .

# Собираем статику
RUN python manage.py collectstatic --noinput

# Открываем порты для Gunicorn (HTTP) и Daphne (WebSocket)
EXPOSE 8000
EXPOSE 8001

# Запускаем Daphne как основной процесс
CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "connect_u.asgi:application"]
