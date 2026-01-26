# T2 Project

Vue 3 веб-интерфейс для работы с LLM моделями GigaChat, Cotype и T-Pro
## Структура проекта

```
frontend/
├── node_modules/          # Зависимости npm
├── public/               # Статические файлы
├── src/                  
│   ├── components/       # Vue компоненты
│   ├── router/          # Маршрутизация (Vue Router)
│   │    └── index.ts         
│   ├── services/        # Сервисы для работы с API
│   │   └── api.ts        
│   ├── styles/          # Глобальные стили
│   │   └── main.css       
│   ├── tests/           # Тесты
│    │   └── App.spec.ts    
│   ├── views/           # Страницы приложения
│   ├── App.vue          # Корневой компонент
│   └── main.ts          # Точка входа
├── env/                 # Переменные окружения
├── env.d.ts             # Объявления TypeScript
├── index.html           # HTML шаблон
├── package.json         # Зависимости и скрипты
├── package-lock.json    # Лок версий зависимостей
├── postcss.config.js    # Конфигурация PostCSS
├── README.md            # Эта документация
├── tailwind.config.js   # Конфигурация TailwindCSS
├── tsconfig.json        # Конфигурация TypeScript
├── vite.config.ts       # Конфигурация Vite
└── vitest.config.ts     # Конфигурация тестов
```

## Быстрый старт

### 1. Настройка окружения

```bash
# Переход в папку frontend
cd frontend

# Установка зависимостей
npm install

# Запуск dev сервера
npm run dev
```

### 2. Тестирование моделей

```bash
npm run test
```

### 3. Запуск бенчмарка

```bash
python ml/benchmarks/llm_benchmark.py --iterations 5
```


## Требования

- Node.js 18+ 
- npm 9
- Современный браузер (Chrome 90+, Firefox 88+, Safari 14+)



