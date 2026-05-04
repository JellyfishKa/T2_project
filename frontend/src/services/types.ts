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
  has_comparison: boolean
  created_at: string
}

export interface RouteDetails extends Route {
  locations_sequence?: string[]
  locations_data?: Location[]
  metrics?: Metric[]
}

// ─── Vehicles ────────────────────────────────────────────────────────────────
export interface Vehicle {
  id: string
  name: string
  fuel_price_rub: number
  consumption_city_l_100km: number
  consumption_highway_l_100km: number
}

export type TransportMode = 'car' | 'taxi' | 'bus'

// ─── Sales Reps ─────────────────────────────────────────────────────────────
export interface SalesRep {
  id: string
  name: string
  status: 'active' | 'sick' | 'vacation' | 'unavailable'
  vehicle_id: string | null
  vehicle_name: string | null
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
  current_location_ids?: string[]
  original_location_ids?: string[]
  route_source?: 'generated' | 'ai' | 'manual'
  route_label?: string | null
  route_updated_at?: string | null
  has_route_override?: boolean
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

export interface TradePointParams {
  id: string;
  category: string;
  latitude: number;
  longitude: number;
}

export interface GenerateOptimizedScheduleRequest {
  month: string;
  reps: string[];
  trade_points: TradePointParams[];
  max_visits_per_day?: number;
  async_mode?: boolean;
  force?: boolean;
  osrm_url?: string;
}

export interface GenerateOptimizedScheduleAccepted {
  status: string;
  job_id: string;
}

export interface GenerateOptimizedScheduleResult {
  status: string;
  month: string;
  reps: string[];
  created_at: string;
  total_distance_km: number;
  days: any[];
  meta: any;
}

export interface GenerateOptimizedScheduleJobStatus {
  status: string;
  job_id: string;
  result?: GenerateOptimizedScheduleResult;
  error?: string;
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
  return_time: string | null
  created_at: string
}

// ─── Skipped Visit Stash ─────────────────────────────────────────────────────
export interface SkippedStashItem {
  id: string
  visit_schedule_id: string | null
  location_id: string
  location_name: string
  location_category: 'A' | 'B' | 'C' | 'D' | null
  rep_id: string
  rep_name: string
  original_date: string
  resolution: string | null
  resolved_at: string | null
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

// ─── Visit Log ────────────────────────────────────────────────────────────────
export interface VisitLog {
  id: string
  location_id: string
  rep_id: string
  visited_date: string
  schedule_id: string | null
  time_in: string | null   // "HH:MM:SS"
  time_out: string | null  // "HH:MM:SS"
  notes: string | null
  created_at: string
}

// ─── Route Variants (оптимизация с выбором) ──────────────────────────────────
export interface RouteVariantMetrics {
  distance_km: number
  time_hours: number
  cost_rub: number
  quality_score: number
}

export interface RouteVariant {
  id: number
  name: string
  description: string
  algorithm: string
  pros: string[]
  cons: string[]
  locations: string[]           // упорядоченные ID точек
  metrics: RouteVariantMetrics
}

export interface OptimizeVariantsResponse {
  variants: RouteVariant[]
  model_used: string
  response_time_ms: number
  llm_evaluation_success: boolean
}

export interface ConfirmVariantRequest {
  name: string
  locations: string[]
  total_distance_km: number
  total_time_hours: number
  total_cost_rub: number
  quality_score: number
  model_used: string
  original_location_ids: string[]
  original_total_distance_km: number | null
  original_total_time_hours: number | null
  original_total_cost_rub: number | null
}

export interface RoutePreviewPoint {
  lat: number
  lon: number
}

export interface RoutePreviewResponse {
  geometry: Array<[number, number]>
  distance_km: number
  time_minutes: number
  cost_rub: number
  traffic_lights_count: number
  source: string
  transport_mode: TransportMode
}

// ─── Holiday ──────────────────────────────────────────────────────────────────
export interface Holiday {
  date: string       // "YYYY-MM-DD"
  name: string
  is_working: boolean
}

export interface HolidayPatchResponse extends Holiday {
  affected_visits_count: number
}

export interface DayRouteOverrideRequest {
  rep_id: string
  date: string
  location_ids: string[]
  original_location_ids?: string[]
  source: 'ai' | 'manual'
  label?: string
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

export interface BenchmarkRunResponse {
  status: string
  task_id: string
  mode: string
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
  database?: string
  services: {
    database: string
    qwen: 'loaded' | 'not_loaded' | 'available' | 'unavailable' | 'error'
    llama: 'loaded' | 'not_loaded' | 'available' | 'unavailable' | 'error'
  }
  disk_free_mb?: number
  visits_today?: number
  version?: string
}

export interface SalesRepResponse {
  id: string
  name: string
  status: 'active' | 'sick' | 'vacation' | 'unavailable'
  created_at: string
  warning?: string | null
  pending_visits_count?: number
}

export interface ApiError {
  error: string
  message: string
  code?: string
  details?: Record<string, any>
}

export interface AuditLogItem {
  id: string
  action: string
  action_label: string
  table_name: string
  record_id: string | null
  old_value: string | null
  new_value: string | null
  details: string | null
  created_at: string | null
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

// ─── Route Comparison ────────────────────────────────────────────────────────
export interface ComparisonPoint {
  id: string
  name: string
  lat: number
  lon: number
  order: number
  address: string | null
  category: string | null
}

export interface ComparisonDiff {
  distance_delta_km: number
  time_delta_hours: number
  cost_delta_rub: number
  changed_stops_count: number
  improvement_percentage: number
}

export interface RouteComparison {
  route_id: string
  original: ComparisonPoint[]
  current: ComparisonPoint[]
  diff: ComparisonDiff
  model_used: string
  created_at: string | null
}
