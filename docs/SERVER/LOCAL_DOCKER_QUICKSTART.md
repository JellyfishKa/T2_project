# Локальный запуск через Docker (очень коротко)

## 1) Подготовка

Убедитесь, что запущен Docker Desktop.

```bash
docker --version
docker compose version
```

## 2) Настройка `.env`

В каталоге `backend`:

```bash
cp .env.server.example .env
```

Минимально заполните в `backend/.env`:

- `DATABASE_PASSWORD`
- `SECURITY_API_KEY`
- `SECURITY_ADMIN_API_KEY`
- `CORS_ORIGINS`

Если локально без API-ключей, установите:

```env
SECURITY_ENABLE_API_KEY_AUTH=false
```

## 3) Поднять backend-стек

Из корня репозитория:

```bash
docker compose up -d postgres backend
```

Проверка:

```bash
curl http://127.0.0.1:8000/health
```

## 4) (Опционально) Поднять frontend

```bash
docker compose up -d frontend
```

Frontend: `http://127.0.0.1`

## 5) Остановить

```bash
docker compose down
```

Чтобы удалить тома БД:

```bash
docker compose down -v
```
