// ─── Location ───────────────────────────────────────────────────────────────
export interface Location {
  id: string
  name: string
  lat: number
  lon: number
  time_window_start: string
  time_window_end: string
  // Новые поля (Фаза 1)
  category: 'A' | 'B' | 'C' | 'D' | null
  city: string | null
  district: string | null
  address: string | null
}

// ─── Route (оптимизация) ────────────────────────────────────────────────────
export interface Route {
  id: string
  name: string
  locations: string[] // IDs of locations
  total_distance_km: number
  total_time_hours: number
  total_cost_rub: number
  model_used: string
  fallback_reason: string | null
  created_at: string
}

export interface RouteDetails extends Route {
  locations_sequence: string[]
  locations_data: Location[]
}

// ─── Sales Reps ─────────────────────────────────────────────────────────────
export interface SalesRep {
  id: string
  name: string
  status: 'active' | 'sick' | 'vacation' | 'unavailable'
  created_at: string
}

// ─── Schedule ────────────────────────────────────────────────────────────────
export interface VisitScheduleItem {
  id: string
  location_id: string
  location_name: string
  location_category: 'A' | 'B' | 'C' | 'D' | null
  rep_id: string
  rep_name: string
  planned_date: string
  status: 'planned' | 'completed' | 'skipped' | 'rescheduled' | 'cancelled'
  time_in?: string | null   // "HH:MM" — время прихода
  time_out?: string | null  // "HH:MM" — время выхода
}

export interface DailyRoute {
  rep_id: string
  rep_name: string
  date: string
  visits: VisitScheduleItem[]
  total_tt: number
  estimated_duration_hours: number
  lunch_break_at?: string  // "HH:MM"
}

export interface MonthlyPlan {
  month: string
  routes: DailyRoute[]
  total_tt_planned: number
  coverage_pct: number
}

// ─── Force Majeure ──────────────────────────────────────────────────────────
export interface ForceMajeureEvent {
  id: string
  type: 'illness' | 'weather' | 'vehicle_breakdown' | 'other'
  rep_id: string
  rep_name: string
  event_date: string
  description: string | null
  affected_tt_count: number
  redistributed_to: Array<{
    rep_id: string
    rep_name: string
    location_ids: string[]
    new_date: string
  }>
  created_at: string
}

// ─── Insights ────────────────────────────────────────────────────────────────
export interface Insights {
  month: string
  total_tt: number
  coverage_pct: number
  visits_this_month: {
    planned: number
    completed: number
    completion_rate: number
  }
  by_category: Record<
    'A' | 'B' | 'C' | 'D',
    {
      total: number
      planned: number
      completed: number
      pct: number
    }
  >
  by_district: Array<{
    district: string
    total: number
    coverage_pct: number
  }>
  rep_activity: Array<{
    rep_id: string
    rep_name: string
    outings_count: number
    tt_visited: number
  }>
  force_majeure_count: number
}

// ─── Metrics / Benchmark ─────────────────────────────────────────────────────
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
    lat: number
    lon: number
  }>
  num_iterations: number
}

export interface OptimizeRequest {
  location_ids: string[]
  model?: string
  constraints?: {
    max_stops_per_route?: number
    time_window_minutes?: number
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
    qwen: 'connected' | 'available' | 'unavailable' | 'error'
    llama: 'connected' | 'available' | 'unavailable' | 'error'
  }
}

export interface ApiError {
  error: string
  message: string
  code?: string
  details?: Record<string, any>
}

export interface ModelComparison {
  models: Array<{
    name: string
    avg_response_time_ms: number
    avg_quality_score: number
    total_cost_rub: number
    success_rate: number
    usage_count: number
  }>
  recommendations: Array<{
    scenario: string
    recommended_model: string
    reason: string
  }>
}
