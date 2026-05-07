#!/bin/bash
set -e

# Накатываем миграции
# Путь к конфигу указываем явно через -c
echo "Running migrations..."
alembic -c src/database/alembic.ini upgrade head

# Запускаем само приложение
echo "Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1