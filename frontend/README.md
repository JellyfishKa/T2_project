# T2 Project

Vue 3 веб-интерфейс для работы с LLM моделями Qwen и Llama
## Структура проекта

```
frontend/
├── src/
│   ├── components/           # Компоненты
│   │   ├── dashboard/        # Компоненты дашборда
│   │   │   ├── HealthStatus.vue
│   │   │   ├── MetricCard.vue
│   │   │   ├── MetricsTable.vue
│   │   │   ├── ModelComparison.vue
│   │   │   ├── RouteList.vue
│   │   │   └── RouteMetrics.vue
│   │   ├── optimize/         # Компоненты оптимизации
│   │   │   ├── ConstraintsPanel.vue
│   │   │   ├── FileUpload.vue
│   │   │   ├── LocationInput.vue
│   │   │   ├── OptimizationForm.vue
│   │   │   ├── OptimizationResult.vue
│   │   │   └── types.ts
│   │   ├── Header.vue
│   │   ├── Layout.vue
│   │   ├── RouteMap.vue
│   │   └── Sidebar.vue     
│   ├── views/                 # Страницы
│   │   ├── HomeView.vue
│   │   ├── DashboardView.vue
│   │   ├── OptimizeView.vue
│   │   └── AnalyticsView.vue
│   ├── services/              # API сервисы
│   │   ├── api.ts            # Основной API клиент
│   │   └── types.ts          # TypeScript типы
│   ├── router/                # Маршрутизация
│   │   └── index.ts
│   ├── tests/                 # Тесты
│   │   ├── views/
│   │   ├── components/
│   │   │   └── dashboard/
│   │   │   └── optimize/
│   │   ├── integration/
│   │   │   └── front-backend.spec.ts  
│   │   ├── services/
│   │   └── setup.js
│   ├── styles/                 # Глобальные стили
│   │   └── main.css
│   ├── App.vue
│   └── main.ts
├── .env                        # Переменные окружения (разработка)
├── .env.production             # Переменные окружения (продакшн)
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── vitest.config.ts
├── tailwind.config.js
├── postcss.config.js
└── README.md
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

# Форматирование кода
```bash
npx prettier --check src/
```

## Требования

- Node.js 18+ 
- npm 9
- Современный браузер (Chrome 90+, Firefox 88+, Safari 14+)



