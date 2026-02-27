import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios'
import type {
  Location,
  Route,
  RouteDetails,
  Metric,
  BenchmarkResult,
  BenchmarkRequest,
  OptimizeRequest,
  PaginatedResponse,
  HealthStatus,
  ApiError,
  Insights,
  ModelComparison,
  SalesRep,
  MonthlyPlan,
  ForceMajeureEvent,
  VisitScheduleItem
} from './types'

// Конфигурация API
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000, // 30 секунд
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json'
  }
}

// Создаем экземпляр axios
const api: AxiosInstance = axios.create(API_CONFIG)

// ========== НАСТРОЙКИ ПОВТОРНЫХ ПОПЫТОК ==========
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 секунда

// Функция для задержки
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

// Функция для повторных попыток
async function withRetry<T>(
  fn: () => Promise<T>,
  retries: number = MAX_RETRIES
): Promise<T> {
  try {
    return await fn()
  } catch (error) {
    const axiosError = error as AxiosError

    // Retry только на 5xx ошибки (серверные)
    if (
      retries > 0 &&
      axiosError.response?.status &&
      axiosError.response.status >= 500
    ) {
      console.log(`Retrying... ${MAX_RETRIES - retries + 1}/${MAX_RETRIES}`)
      await delay(RETRY_DELAY)
      return withRetry(fn, retries - 1)
    }

    // Пробрасываем ошибку дальше
    throw error
  }
}

// ========== ТИПЫ ДЛЯ ОТВЕТОВ ==========
export interface UploadLocationsResponse {
  success: boolean
  message: string
  locations: Location[]
  errors?: Array<{
    row: number
    field: string
    message: string
  }>
}

// ========== ИНТЕРСЕПТОРЫ ==========
// Интерсептор для обработки ошибок
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError<ApiError>) => {
    // Обработка timeout
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout:', error.message)
      return Promise.reject({
        error: 'Timeout Error',
        message:
          'Запрос занял слишком много времени. Пожалуйста, попробуйте снова.',
        code: 'TIMEOUT_ERROR'
      })
    }

    // Обработка сетевых ошибок
    if (!error.response) {
      console.error('Network error:', error.message)
      return Promise.reject({
        error: 'Network Error',
        message:
          'Не удалось подключиться к серверу. Проверьте интернет-соединение.',
        code: 'NETWORK_ERROR'
      })
    }

    const { status, data } = error.response

    // Логируем ошибки для отладки
    switch (status) {
      case 400:
        console.error('Bad Request:', data)
        break
      case 401:
        console.error('Unauthorized:', data)
        break
      case 403:
        console.error('Forbidden:', data)
        break
      case 404:
        console.error('Not Found:', data)
        break
      case 422:
        console.error('Validation Error:', data)
        break
      case 429:
        console.error('Too Many Requests:', data)
        break
      case 500:
        console.error('Internal Server Error:', data)
        break
      case 502:
      case 503:
      case 504:
        console.error('Service Unavailable:', data)
        break
      default:
        console.error(`HTTP Error ${status}:`, data)
    }

    return Promise.reject(error.response?.data || error)
  }
)

// ========== REAL API ФУНКЦИИ ==========

/**
 * Загрузка файла с локациями
 * POST /api/v1/locations/upload
 */
export const uploadLocations = async (
  file: File
): Promise<UploadLocationsResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await withRetry(() =>
    api.post('/locations/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  )
  return response.data
}

/**
 * Оптимизация маршрута
 * POST /api/v1/optimize
 */
export const optimize = async (
  locationIds: string[],
  model: string,
  constraints: any
): Promise<Route> => {
  const request = {
    location_ids: locationIds,
    model: model,
    constraints: constraints
  }

  const response = await withRetry(() => api.post('/optimize', request))
  return response.data
}

/**
 * Получение метрик
 * GET /api/v1/metrics
 */
export const getMetrics = async (): Promise<{ metrics: Metric[] }> => {
  const response = await withRetry(() => api.get('/metrics'))
  return response.data
}

/**
 * Получение инсайтов
 * GET /api/v1/insights
 */
export const getInsights = async (): Promise<Insights> => {
  const response = await withRetry(() => api.get('/insights'))
  return response.data
}

/**
 * Сравнение моделей
 * GET /api/v1/benchmark/compare
 */
export const compareModels = async (): Promise<ModelComparison> => {
  const response = await withRetry(() => api.get('/benchmark/compare'))
  return response.data
}

/**
 * Получение списка маршрутов
 * GET /api/v1/routes
 */
export const fetchRoutes = async (
  skip: number = 0,
  limit: number = 10
): Promise<PaginatedResponse<Route>> => {
  const response = await withRetry(() =>
    api.get('/routes', { params: { skip, limit } })
  )
  return response.data
}

/**
 * Получение деталей маршрута
 * GET /api/v1/routes/{route_id}
 *
 * ВНИМАНИЕ: Этот endpoint возвращает RouteDetails с полями locations_sequence и locations_data
 */
export const fetchRouteDetails = async (
  routeId: string
): Promise<RouteDetails> => {
  const response = await withRetry(() => api.get(`/routes/${routeId}`))
  return response.data
}

/**
 * Получение метрик для конкретного маршрута
 * GET /api/v1/metrics?route_id={route_id}
 */
export const fetchRouteMetrics = async (
  routeId: string
): Promise<{ metrics: Metric[] }> => {
  const response = await withRetry(() =>
    api.get('/metrics', { params: { route_id: routeId } })
  )
  return response.data
}

/**
 * Запуск бенчмарка
 * POST /api/v1/benchmark
 */
export const runBenchmark = async (
  request: BenchmarkRequest
): Promise<{
  total_duration_seconds: number
  results: BenchmarkResult[]
}> => {
  const response = await withRetry(() => api.post('/benchmark', request))
  return response.data
}

/**
 * Проверка здоровья сервиса
 * GET /api/v1/health
 */
export const checkHealth = async (): Promise<HealthStatus> => {
  try {
    const response = await withRetry(() => api.get('/health'))
    return response.data
  } catch (error) {
    // Если сервер недоступен, возвращаем unhealthy статус
    if ((error as AxiosError).response?.status === 503) {
      return (error as AxiosError).response?.data as HealthStatus
    }
    throw error
  }
}

/**
 * Получение всех локаций
 * GET /api/v1/locations
 */
export const fetchAllLocations = async (): Promise<Location[]> => {
  const response = await withRetry(() => api.get('/locations'))
  return response.data
}

// ========== СОТРУДНИКИ ==========

export const fetchReps = async (): Promise<SalesRep[]> => {
  const response = await withRetry(() => api.get('/reps/'))
  return response.data
}

export const createRep = async (
  name: string,
  status: SalesRep['status'] = 'active'
): Promise<SalesRep> => {
  const response = await withRetry(() =>
    api.post('/reps/', { name, status })
  )
  return response.data
}

export const updateRep = async (
  repId: string,
  data: Partial<Pick<SalesRep, 'name' | 'status'>>
): Promise<SalesRep> => {
  const response = await withRetry(() => api.patch(`/reps/${repId}`, data))
  return response.data
}

export const deleteRep = async (repId: string): Promise<void> => {
  await withRetry(() => api.delete(`/reps/${repId}`))
}

// ========== РАСПИСАНИЕ ==========

export const generateSchedule = async (
  month: string,
  repIds?: string[]
): Promise<{ total_visits_planned: number; coverage_pct: number }> => {
  const response = await withRetry(() =>
    api.post('/schedule/generate', { month, rep_ids: repIds })
  )
  return response.data
}

export const fetchMonthlySchedule = async (
  month: string
): Promise<MonthlyPlan> => {
  const response = await withRetry(() =>
    api.get('/schedule/', { params: { month } })
  )
  return response.data
}

export const fetchRepSchedule = async (
  repId: string,
  month: string
): Promise<MonthlyPlan> => {
  const response = await withRetry(() =>
    api.get(`/schedule/${repId}`, { params: { month } })
  )
  return response.data
}

// ========== ВИЗИТЫ: ОБНОВЛЕНИЕ СТАТУСА ==========

export const updateVisitStatus = async (
  visitId: string,
  data: {
    status: 'completed' | 'skipped' | 'cancelled' | 'rescheduled' | 'planned'
    time_in?: string
    time_out?: string
    notes?: string
  }
): Promise<VisitScheduleItem> => {
  const response = await withRetry(() =>
    api.patch(`/schedule/${visitId}`, data)
  )
  return response.data
}

// ========== ФОРС-МАЖОРЫ ==========

export const createForceMajeure = async (data: {
  type: string
  rep_id: string
  event_date: string
  description?: string
}): Promise<ForceMajeureEvent> => {
  const response = await withRetry(() => api.post('/force_majeure/', data))
  return response.data
}

export const fetchForceMajeure = async (
  month: string
): Promise<ForceMajeureEvent[]> => {
  const response = await withRetry(() =>
    api.get('/force_majeure/', { params: { month } })
  )
  return response.data
}

export { api }
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
  ApiError,
  Insights,
  ModelComparison,
  SalesRep,
  MonthlyPlan,
  ForceMajeureEvent,
  VisitScheduleItem
}
