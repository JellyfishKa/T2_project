// Типы данных согласно API_CONTRACT.md

export interface Location {
  id: string
  name: string
  latitude: number
  longitude: number
  address: string
  time_window_start: string
  time_window_end: string
  priority: number
}

export interface Route {
  id: string
  name: string
  locations: string[] // IDs of locations
  total_distance_km: number
  total_time_hours: number
  total_cost_rub: number
  model_used: string
  created_at: string
}

export interface RouteDetails extends Route {
  locations_sequence: string[]
  locations_data: Location[]
}

export interface Metric {
  id: string
  route_id: string
  model: string
  response_time_ms: number
  quality_score: number
  cost_rub: number
  timestamp: string
}

export interface BenchmarkResult {
  model: string
  num_tests: number
  avg_response_time_ms: number
  min_response_time_ms: number
  max_response_time_ms: number
  avg_quality_score: number
  total_cost_rub: number
  success_rate: number
  timestamp: string
}

export interface BenchmarkRequest {
  test_locations: Array<{
    id: string
    name: string
    latitude: number
    longitude: number
  }>
  num_iterations: number
}

export interface OptimizeRequest {
  locations: Array<{
    id: string
    name: string
    latitude: number
    longitude: number
    time_window_start: string
    time_window_end: string
  }>
  constraints: {
    vehicle_capacity?: number
    max_distance_km?: number
    start_time?: string
    end_time?: string
  }
}

export interface PaginatedResponse<T> {
  total: number
  items: T[]
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  services: {
    database: 'connected' | 'disconnected'
    llama: 'connected' | 'available' | 'unavailable' | 'error'
    qwen: 'connected' | 'available' | 'unavailable' | 'error'
    tpro: 'connected' | 'available' | 'unavailable' | 'error'
  }
}

export interface ApiError {
  error: string
  message: string
  code?: string
  details?: Record<string, any>
}
