import { Location, Route, Metric, BenchmarkResult, HealthStatus } from './types'

// Салоны Т2 в Саранске и районах Мордовии
export const mockLocations: Location[] = [
  {
    id: 'store-1',
    name: 'Салон Т2 Саранск Центр',
    latitude: 54.1871,
    longitude: 45.1749,
    address: 'ул. Советская, 35, Саранск',
    time_window_start: '09:00',
    time_window_end: '18:00',
    priority: 1
  },
  {
    id: 'store-2',
    name: 'Салон Т2 Проспект Ленина',
    latitude: 54.1902,
    longitude: 45.1685,
    address: 'пр. Ленина, 15, Саранск',
    time_window_start: '09:00',
    time_window_end: '18:00',
    priority: 1
  },
  {
    id: 'store-3',
    name: 'Салон Т2 Огарев Plaza',
    latitude: 54.1845,
    longitude: 45.1695,
    address: 'ул. Большевистская, 84, Саранск',
    time_window_start: '10:00',
    time_window_end: '20:00',
    priority: 1
  },
  {
    id: 'store-4',
    name: 'Салон Т2 Победы',
    latitude: 54.1935,
    longitude: 45.1620,
    address: 'ул. Победы, 120, Саранск',
    time_window_start: '10:00',
    time_window_end: '21:00',
    priority: 2
  },
  {
    id: 'store-5',
    name: 'Салон Т2 Рузаевка',
    latitude: 54.0620,
    longitude: 44.9500,
    address: 'ул. Ленина, 1, Рузаевка',
    time_window_start: '09:00',
    time_window_end: '17:00',
    priority: 2
  },
  {
    id: 'store-6',
    name: 'Салон Т2 Ковылкино',
    latitude: 54.0380,
    longitude: 43.9190,
    address: 'ул. Свердлова, 12, Ковылкино',
    time_window_start: '09:00',
    time_window_end: '17:00',
    priority: 2
  }
]

// Оптимизированные маршруты по Мордовии
export const mockRoutes: Route[] = [
  {
    id: 'route-1',
    name: 'Центральный Саранск',
    locations: ['store-1', 'store-2', 'store-3'],
    total_distance_km: 4.2,
    total_time_hours: 1.5,
    total_cost_rub: 294,
    model_used: 'qwen',
    fallback_reason: null,
    created_at: '2026-02-20T09:15:00Z'
  },
  {
    id: 'route-2',
    name: 'Саранск — Рузаевка',
    locations: ['store-1', 'store-5'],
    total_distance_km: 25.4,
    total_time_hours: 2.8,
    total_cost_rub: 1778,
    model_used: 'qwen',
    fallback_reason: null,
    created_at: '2026-02-19T14:30:00Z'
  },
  {
    id: 'route-3',
    name: 'Западный маршрут',
    locations: ['store-5', 'store-6'],
    total_distance_km: 42.3,
    total_time_hours: 5.0,
    total_cost_rub: 2961,
    model_used: 'llama',
    fallback_reason: null,
    created_at: '2026-02-18T11:45:00Z'
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
  {
    id: 'metric-5',
    route_id: 'route-2',
    model: 'qwen',
    response_time_ms: 410,
    quality_score: 0.81,
    cost_rub: 0.0,
    timestamp: '2026-01-05T14:32:00Z'
  },
  // Метрики для route-3
  {
    id: 'metric-7',
    route_id: 'route-3',
    model: 'llama',
    response_time_ms: 1300,
    quality_score: 0.86,
    cost_rub: 24.0,
    timestamp: '2026-01-04T11:47:00Z'
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
]

// Health status
export const mockHealthStatus: HealthStatus = {
  status: 'healthy',
  services: {
    database: 'connected',
    llama: 'connected',
    qwen: 'available',
  }
}

// Helper functions
export const generateMockRoute = (): Route => {
  const routeId = `route-${Date.now()}`
  const useFallback = Math.random() > 0.7

  return {
    id: routeId,
    name: `Маршрут ${new Date().toLocaleTimeString()}`,
    locations: ['store-1', 'store-2'],
    total_distance_km: 15.5 + Math.random() * 10,
    total_time_hours: 1.5 + Math.random() * 2,
    total_cost_rub: 1200 + Math.random() * 1000,
    model_used: 'llama',
    fallback_reason: useFallback ? 'Primary model overloaded' : null,
    created_at: new Date().toISOString()
  }
}

export const simulateDelay = (ms = 500): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
