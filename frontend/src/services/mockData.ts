import { Location, Route, Metric, BenchmarkResult, HealthStatus } from './types'

// 5+ магазинов с координатами Москвы
export const mockLocations: Location[] = [
  {
    id: 'store-1',
    name: 'ТЦ Авиапарк',
    latitude: 55.7979,
    longitude: 37.5352,
    address: 'Ходынский бульвар, 4, Москва',
    time_window_start: '09:00',
    time_window_end: '22:00',
    priority: 1
  },
  {
    id: 'store-2',
    name: 'ТЦ Европейский',
    latitude: 55.7358,
    longitude: 37.524,
    address: 'Площадь Киевского Вокзала, 2, Москва',
    time_window_start: '10:00',
    time_window_end: '22:00',
    priority: 1
  },
  {
    id: 'store-3',
    name: 'ТЦ Метрополис',
    latitude: 55.8286,
    longitude: 37.3945,
    address: 'Ленинградское ш., 16А, стр. 4, Москва',
    time_window_start: '10:00',
    time_window_end: '21:00',
    priority: 2
  },
  {
    id: 'store-4',
    name: 'ТЦ Афимолл Сити',
    latitude: 55.7486,
    longitude: 37.5388,
    address: 'Пресненская наб., 2, Москва',
    time_window_start: '10:00',
    time_window_end: '22:00',
    priority: 1
  },
  {
    id: 'store-5',
    name: 'ТЦ Вегас',
    latitude: 55.5697,
    longitude: 37.8023,
    address: 'МКАД, 24-й км, вл. 1, Москва',
    time_window_start: '09:00',
    time_window_end: '23:00',
    priority: 3
  },
  {
    id: 'store-6',
    name: 'ТЦ Ривьера',
    latitude: 55.7066,
    longitude: 37.6402,
    address: 'Автозаводская ул., 18, Москва',
    time_window_start: '10:00',
    time_window_end: '22:00',
    priority: 2
  }
]

// 2-3 оптимизированных маршрутов
export const mockRoutes: Route[] = [
  {
    id: 'route-1',
    name: 'Центральный маршрут',
    locations: ['store-1', 'store-2', 'store-4'],
    total_distance_km: 28.5,
    total_time_hours: 3.2,
    total_cost_rub: 1850,
    model_used: 'llama',
    created_at: '2026-01-06T09:15:00Z'
  },
  {
    id: 'route-2',
    name: 'Северо-Западный маршрут',
    locations: ['store-3', 'store-1'],
    total_distance_km: 35.7,
    total_time_hours: 4.1,
    total_cost_rub: 2100,
    model_used: 'qwen',
    created_at: '2026-01-05T14:30:00Z'
  },
  {
    id: 'route-3',
    name: 'Южный маршрут',
    locations: ['store-5', 'store-6'],
    total_distance_km: 42.3,
    total_time_hours: 5.5,
    total_cost_rub: 2750,
    model_used: 'tpro',
    created_at: '2026-01-04T11:45:00Z'
  }
]

// Метрики для каждого маршрута
export const mockMetrics: Metric[] = [
  // Метрики для route-1 (llama)
  {
    id: 'metric-1',
    route_id: 'route-1',
    model: 'llama',
    response_time_ms: 1245,
    quality_score: 0.87,
    cost_rub: 25.5,
    timestamp: '2026-01-06T09:15:30Z'
  },
  {
    id: 'metric-2',
    route_id: 'route-1',
    model: 'qwen',
    response_time_ms: 432,
    quality_score: 0.82,
    cost_rub: 0.0,
    timestamp: '2026-01-06T09:16:15Z'
  },
  {
    id: 'metric-3',
    route_id: 'route-1',
    model: 'tpro',
    response_time_ms: 1850,
    quality_score: 0.89,
    cost_rub: 18.0,
    timestamp: '2026-01-06T09:17:00Z'
  },
  // Метрики для route-2
  {
    id: 'metric-4',
    route_id: 'route-2',
    model: 'llama',
    response_time_ms: 1120,
    quality_score: 0.85,
    cost_rub: 22.0,
    timestamp: '2026-01-05T14:31:00Z'
  },
  // Метрики для route-3
  {
    id: 'metric-5',
    route_id: 'route-3',
    model: 'tpro',
    response_time_ms: 1950,
    quality_score: 0.88,
    cost_rub: 20.0,
    timestamp: '2026-01-04T11:46:00Z'
  }
]

// Результаты бенчмарков для 3 моделей
export const mockBenchmarkResults: BenchmarkResult[] = [
  {
    model: 'llama',
    num_tests: 10,
    avg_response_time_ms: 1250,
    min_response_time_ms: 850,
    max_response_time_ms: 2100,
    avg_quality_score: 0.87,
    total_cost_rub: 250.0,
    success_rate: 1.0,
    timestamp: '2026-01-06T11:00:00Z'
  },
  {
    model: 'qwen',
    num_tests: 10,
    avg_response_time_ms: 450,
    min_response_time_ms: 350,
    max_response_time_ms: 650,
    avg_quality_score: 0.82,
    total_cost_rub: 0.0,
    success_rate: 1.0,
    timestamp: '2026-01-06T11:00:00Z'
  },
  {
    model: 'tpro',
    num_tests: 10,
    avg_response_time_ms: 1800,
    min_response_time_ms: 1200,
    max_response_time_ms: 2400,
    avg_quality_score: 0.89,
    total_cost_rub: 180.0,
    success_rate: 0.9,
    timestamp: '2026-01-06T11:00:00Z'
  }
]

// Health status
export const mockHealthStatus: HealthStatus = {
  status: 'healthy',
  services: {
    database: 'connected',
    llama: 'connected',
    qwen: 'available',
    tpro: 'unavailable'
  }
}

// Helper functions
export const generateMockRoute = () => {
  const routeId = `route-${Date.now()}`
  return {
    route_id: routeId,
    locations_sequence: ['store-1', 'store-2'],
    total_distance_km: 15.5 + Math.random() * 10,
    total_time_hours: 1.5 + Math.random() * 2,
    total_cost_rub: 1200 + Math.random() * 1000,
    model_used: 'llama',
    created_at: new Date().toISOString()
  }
}

export const simulateDelay = (ms = 500): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
