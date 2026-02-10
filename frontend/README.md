# T2 Project

Vue 3 веб-интерфейс для работы с LLM моделями Llama, Qwen и T-Pro
## Структура проекта

```
frontend/
├── src/
│   ├── components/
│   │   ├── dashboard/          # Компоненты дашборда
│   │   │   ├── MetricCard.vue      
│   │   │   ├── MetricsTable.vue   
│   │   │   ├── ModelComparison.vue 
│   │   │   ├── RouteList.vue      
│   │   │   ├── RouteMetrics.vue   
│   │   │   └── HealthStatus.vue   
│   │   ├── optimize/           # Компоненты оптимизации
│   │   │   ├── ConstraintsPanel.vue # Панель ограничений
│   │   │   ├── FileUpload.vue      
│   │   │   ├── LocationInput.vue    
│   │   │   └── OptimizationForm.vue 
│   │   ├── types.ts            
│   │   ├── Header.vue        
│   │   ├── Layout.vue         
│   │   ├── RouteMap.vue        
│   │   └── Sidebar.vue         
│   ├── views/                  # Страницы приложения
│   │   ├── HomeView.vue        
│   │   ├── DashboardView.vue   
│   │   ├── OptimizeView.vue    
│   │   └── AnalyticsView.vue   
│   ├── services/               # Сервисы API
│   │   ├── api.ts             
│   │   └── mockData.ts        
│   ├── router/                 # Маршрутизация
│   │   └── index.ts
│   ├── tests/                  # Тесты
│   │   ├── components/       
│   │   ├── views/              
│   │   └── services/           
│   ├── styles/                 # Глобальные стили
│   │   └── main.css
│   ├── App.vue                 
│   └── main.ts              
├── package.json               # Зависимости
├── tsconfig.json              # TypeScript конфиг
├── vite.config.ts             # Vite конфиг
├── tailwind.config.js         # Tailwind конфиг
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


## Требования

- Node.js 18+ 
- npm 9
- Современный браузер (Chrome 90+, Firefox 88+, Safari 14+)



