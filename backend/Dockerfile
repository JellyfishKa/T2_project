# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12 as builder

# Устанавливаем системные зависимости для сборки (если нужны для asyncpg/psycopg2)
RUN apt-get update && apt-get install -y gcc build-essential

WORKDIR /app

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем только requirements для кэширования слоя
COPY requirements/prod/requirements.txt .
RUN pip install --no-cache-dir -r requirements/prod/requirements.txt

# ==========================================
# Stage 2: Final
# ==========================================
FROM python:3.12

WORKDIR /app

# Копируем виртуальное окружение из билдера
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем код приложения
COPY . .

# Команда по умолчанию (будет переопределена в docker-compose для hot-reload)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]