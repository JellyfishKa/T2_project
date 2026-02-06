### Загрузка модели t-pro

1) Скачаем модель по ссылке: 

2) Поместим данную модель в папку models

3) Укажем имя модели в .env файле:

```
    TPRO_API_ENDPOINT=https://api-inference.huggingface.co/v1/chat/completions
    TPRO_MODEL_ID=
```

4) Запустим сервер, проверим работоспособность модели POST-запросом по эндпойнту /tpro/optimize:

    - Выполните curl запрос в следующем виде:
```
curl -X 'POST' \
  'http://127.0.0.1:8000/tpro/optimize' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "locations": [
    {
      "ID": "loc_red_square",
      "name": "Red Square",
      "address": "Red Square, Moscow, Russia",
      "lat": 55.7539,
      "lon": 37.6208,
      "time_window_start": "10:00",
      "time_window_end": "22:00",
      "priority": "high"
    },
    {
      "ID": "loc_gorky_park",
      "name": "Gorky Park",
      "address": "Krymskiy Val, 9, Moscow, Russia",
      "lat": 55.7298,
      "lon": 37.5995,
      "time_window_start": "08:00",
      "time_window_end": "23:00",
      "priority": "medium"
    }
  ],
  "constraints": {}
}'

```