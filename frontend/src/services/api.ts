import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios'
import {
  Location,
  Route,
  RouteDetails,
  Metric,
  BenchmarkResult,
  BenchmarkRequest,
  OptimizeRequest,
  PaginatedResponse,
  HealthStatus,
  ApiError
} from './types'
import {
  mockRoutes,
  mockLocations,
  mockMetrics,
  mockBenchmarkResults,
  mockHealthStatus,
  generateMockRoute,
  simulateDelay
} from './mockData'

// Конфигурация API
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
}

// Функция для определения режима разработки
const isDevelopment = (): boolean => {
  return import.meta.env.MODE === 'development'
}

// ========== MOCK API (для Недели 1) ==========
const mockApi = {
  // 1. Оптимизация маршрута
  optimize: async (request: OptimizeRequest): Promise<any> => {
    await simulateDelay(500)
    console.log('Mock: Optimizing route with', request.locations.length, 'locations')
    return generateMockRoute()
  },

  // 2. Получение списка маршрутов
  fetchRoutes: async (skip: number = 0, limit: number = 10): Promise<PaginatedResponse<Route>> => {
    await simulateDelay(300)
    const items = mockRoutes.slice(skip, skip + limit)
    return {
      total: mockRoutes.length,
      items
    }
  },

  // 3. Получение деталей маршрута
  fetchRouteDetails: async (routeId: string): Promise<RouteDetails> => {
    await simulateDelay(250)
    const route = mockRoutes.find(r => r.id === routeId)
    
    if (!route) {
      throw {
        response: {
          status: 404,
          data: {
            error: 'Маршрут не найден',
            message: `Route with ID ${routeId} not found`,
            route_id: routeId
          }
        }
      }
    }

    return {
      ...route,
      locations_sequence: route.locations,
      locations_data: mockLocations.filter(loc => route.locations.includes(loc.id))
    }
  },

  // 4. Получение метрик
  fetchMetrics: async (routeId?: string): Promise<{ metrics: Metric[] }> => {
    await simulateDelay(350)
    const metrics = routeId 
      ? mockMetrics.filter(m => m.route_id === routeId)
      : mockMetrics
    
    return { metrics }
  },

  // 5. Запуск бенчмарка
  runBenchmark: async (request: BenchmarkRequest): Promise<{
    total_duration_seconds: number
    results: BenchmarkResult[]
  }> => {
    await simulateDelay(800)
    console.log('Mock: Running benchmark with', request.num_iterations, 'iterations')
    return {
      total_duration_seconds: 45.2,
      results: mockBenchmarkResults
    }
  },

  // 6. Проверка здоровья сервиса
  checkHealth: async (): Promise<HealthStatus> => {
    await simulateDelay(100)
    return mockHealthStatus
  },

  // 7. Получение всех локаций
  fetchAllLocations: async (): Promise<Location[]> => {
    await simulateDelay(300)
    return mockLocations
  }
}

// ========== REAL API (для Недели 2) ==========
// Создаем экземпляр axios
const realApi: AxiosInstance = axios.create(API_CONFIG)

// Interceptor для обработки ошибок
realApi.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ApiError>) => {
    if (!error.response) {
      console.error('Network error:', error.message)
      return Promise.reject({
        error: 'Network Error',
        message: 'Unable to connect to the server. Please check your internet connection.',
        code: 'NETWORK_ERROR'
      })
    }

    const { status, data } = error.response
    
    switch (status) {
      case 400:
        console.error('Bad Request:', data)
        break
      case 404:
        console.error('Not Found:', data)
        break
      case 429:
        console.error('Rate Limited:', data)
        break
      case 500:
        console.error('Server Error:', data)
        break
      case 503:
        console.error('Service Unavailable:', data)
        break
      default:
        console.error(`HTTP Error ${status}:`, data)
    }

    return Promise.reject(error.response.data || error)
  }
)

// Функции-обёртки для реального API
const realApiFunctions = {
  optimize: async (request: OptimizeRequest): Promise<any> => {
    const response = await realApi.post('/optimize', request)
    return response.data
  },

  fetchRoutes: async (skip: number = 0, limit: number = 10): Promise<PaginatedResponse<Route>> => {
    const response = await realApi.get('/routes', { params: { skip, limit } })
    return response.data
  },

  fetchRouteDetails: async (routeId: string): Promise<RouteDetails> => {
    const response = await realApi.get(`/routes/${routeId}`)
    return response.data
  },

  fetchMetrics: async (routeId?: string): Promise<{ metrics: Metric[] }> => {
    const params = routeId ? { route_id: routeId } : {}
    const response = await realApi.get('/metrics', { params })
    return response.data
  },

  runBenchmark: async (request: BenchmarkRequest): Promise<{
    total_duration_seconds: number
    results: BenchmarkResult[]
  }> => {
    const response = await realApi.post('/benchmark', request)
    return response.data
  },

  checkHealth: async (): Promise<HealthStatus> => {
    const response = await realApi.get('/health')
    return response.data
  },

  fetchAllLocations: async (): Promise<Location[]> => {
    throw new Error('Endpoint not implemented in backend')
  }
}

// ========== ЕДИНЫЙ ИНТЕРФЕЙС ==========
// Выбираем какой API использовать
const apiFunctions = isDevelopment() ? mockApi : realApiFunctions

// Экспортируемые функции
export const optimizeRoute = apiFunctions.optimize
export const fetchRoutes = apiFunctions.fetchRoutes
export const fetchRouteDetails = apiFunctions.fetchRouteDetails
export const fetchMetrics = apiFunctions.fetchMetrics
export const runBenchmark = apiFunctions.runBenchmark
export const checkHealth = apiFunctions.checkHealth
export const fetchAllLocations = apiFunctions.fetchAllLocations

// Экспортируем axios instance для прямого использования
export const api = realApi

// Экспортируем типы
export type {
  Location,
  Route,
  RouteDetails,
  Metric,
  BenchmarkResult,
  BenchmarkRequest,
  OptimizeRequest,
  PaginatedResponse,
  HealthStatus,
  ApiError
}