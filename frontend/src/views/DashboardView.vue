<template>
  <div class="py-6 md:py-8">
    <!-- Page Header -->
    <div
      class="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900">Dashboard</h1>
        <p class="mt-2 text-gray-600">
          Обзор оптимизированных маршрутов и сравнение производительности
          моделей
        </p>
      </div>
      <button
        @click="refreshAllData"
        :disabled="isRefreshing"
        class="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg
          class="h-4 w-4 mr-2"
          :class="{ 'animate-spin': isRefreshing }"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
        {{ isRefreshing ? 'Обновление...' : 'Обновить все' }}
      </button>
    </div>

    <!-- Error State -->
    <div
      v-if="error"
      class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6"
    >
      <div class="flex">
        <div class="flex-shrink-0">
          <svg
            class="h-5 w-5 text-red-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">
            Ошибка загрузки данных
          </h3>
          <div class="mt-2 text-sm text-red-700">
            <p>{{ error }}</p>
          </div>
          <button
            @click="loadDashboardData"
            class="mt-3 text-sm font-medium text-red-800 hover:text-red-900"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    </div>

    <!-- Main Dashboard Content (only shown when no error) -->
    <template v-else>
      <!-- Health Status -->
      <div v-if="healthStatus" class="mb-6">
        <HealthStatus :status="healthStatus" />
      </div>

      <!-- Route Statistics -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <!-- Total Routes Card -->
        <div
          v-if="!isLoadingStats"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 md:p-6"
        >
          <div class="flex items-center">
            <div class="flex-shrink-0 bg-blue-100 rounded-lg p-3">
              <svg
                class="h-6 w-6 text-blue-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">Всего маршрутов</p>
              <p class="text-2xl font-semibold text-gray-900">
                {{ routes.total || 0 }}
              </p>
            </div>
          </div>
        </div>
        <SkeletonLoader v-else height="120px" />

        <!-- Average Time Card -->
        <div
          v-if="!isLoadingStats"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 md:p-6"
        >
          <div class="flex items-center">
            <div class="flex-shrink-0 bg-green-100 rounded-lg p-3">
              <svg
                class="h-6 w-6 text-green-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">Среднее время</p>
              <p class="text-2xl font-semibold text-gray-900">
                {{ averageTime }} ч
              </p>
            </div>
          </div>
        </div>
        <SkeletonLoader v-else height="120px" />

        <!-- Average Cost Card -->
        <div
          v-if="!isLoadingStats"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 md:p-6"
        >
          <div class="flex items-center">
            <div class="flex-shrink-0 bg-purple-100 rounded-lg p-3">
              <svg
                class="h-6 w-6 text-purple-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">Средняя стоимость</p>
              <p class="text-2xl font-semibold text-gray-900">
                {{ averageCost }} ₽
              </p>
            </div>
          </div>
        </div>
        <SkeletonLoader v-else height="120px" />
      </div>

      <!-- Main Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Routes List -->
        <div class="lg:col-span-2">
          <div class="bg-white rounded-xl shadow-sm border border-gray-200">
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
              <h3 class="text-lg font-semibold text-gray-900">
                Оптимизированные маршруты
              </h3>
              <p class="mt-1 text-sm text-gray-600">
                Список всех созданных маршрутов
              </p>
            </div>
            <div class="px-4 py-5 sm:p-6">
              <RouteList
                :routes="routes.items"
                :is-loading="isLoadingRoutes"
                :selected-route-id="selectedRouteId"
                :sortable="true"
                :sort-field="routeSortField"
                :sort-direction="routeSortDirection"
                @select-route="handleRouteSelect"
                @sort="handleRouteSort"
              />
            </div>
          </div>
        </div>

        <!-- Metrics and Comparison -->
        <div class="space-y-6">
          <!-- Route Metrics -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200">
            <div class="px-6 py-5 sm:px-7 border-b border-gray-200">
              <h3 class="text-lg font-semibold text-gray-900">
                Метрики маршрута
              </h3>
              <p class="mt-1 text-sm text-gray-600">Детальная информация</p>
            </div>
            <div class="px-4 py-5 sm:p-6">
              <RouteMetrics
                :route="selectedRouteDetails"
                :metrics="routeMetrics"
                :is-loading="isLoadingRouteDetails"
              />
            </div>
          </div>

          <!-- Model Comparison -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200">
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
              <h3 class="text-lg font-semibold text-gray-900">
                Сравнение моделей
              </h3>
              <p class="mt-1 text-sm text-gray-600">Производительность LLM</p>
            </div>
            <div class="px-4 py-5 sm:p-6">
              <ModelComparison
                :benchmark-results="modelComparison?.models || []"
                :recommendations="modelComparison?.recommendations || []"
                :is-loading="isLoadingComparison"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Metrics -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 mt-6">
        <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">
                Последние метрики
              </h3>
              <p class="mt-1 text-sm text-gray-600">
                История выполнения оптимизаций
              </p>
            </div>
            <button
              @click="loadMetrics"
              :disabled="isLoadingMetrics"
              class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
                class="h-4 w-4 mr-2"
                :class="{ 'animate-spin': isLoadingMetrics }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              {{ isLoadingMetrics ? 'Загрузка...' : 'Обновить' }}
            </button>
          </div>
        </div>
        <div class="px-4 py-5 sm:p-6">
          <MetricsTable
            :metrics="allMetrics"
            :is-loading="isLoadingMetrics"
            :sortable="true"
            :sort-field="metricsSortField"
            :sort-direction="metricsSortDirection"
            @sort="handleMetricsSort"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import RouteList from '@/components/dashboard/RouteList.vue'
import RouteMetrics from '@/components/dashboard/RouteMetrics.vue'
import ModelComparison from '@/components/dashboard/ModelComparison.vue'
import MetricsTable from '@/components/dashboard/MetricsTable.vue'
import HealthStatus from '@/components/dashboard/HealthStatus.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import {
  fetchRoutes,
  fetchRouteDetails,
  getMetrics,
  compareModels,
  checkHealth,
  type Route,
  type RouteDetails,
  type Metric,
  type ModelComparison as ApiModelComparison,
  type HealthStatus as HealthStatusType,
  type PaginatedResponse
} from '@/services/api'

// Types
type RouteSortField =
  | 'created_at'
  | 'total_distance_km'
  | 'total_time_hours'
  | 'total_cost_rub'
  | 'model_used'
  | 'name'
type MetricsSortField =
  | 'model'
  | 'route_id'
  | 'response_time_ms'
  | 'quality_score'
  | 'cost_rub'
  | 'timestamp'
type SortDirection = 'asc' | 'desc'

// State
const isLoadingStats = ref(true)
const isLoadingRoutes = ref(true)
const isLoadingRouteDetails = ref(false)
const isLoadingMetrics = ref(false)
const isLoadingComparison = ref(true)
const isRefreshing = ref(false)

const error = ref<string | null>(null)

const routes = ref<PaginatedResponse<Route>>({ total: 0, items: [] })
const selectedRouteId = ref<string | null>(null)
const selectedRouteDetails = ref<RouteDetails | null>(null)
const routeMetrics = ref<Metric[]>([])
const allMetrics = ref<Metric[]>([])
const modelComparison = ref<ApiModelComparison | null>(null)
const healthStatus = ref<HealthStatusType | null>(null)

// Sort state
const routeSortField = ref<RouteSortField>('created_at')
const routeSortDirection = ref<SortDirection>('desc')
const metricsSortField = ref<MetricsSortField>('timestamp')
const metricsSortDirection = ref<SortDirection>('desc')

// Computed
const averageTime = computed(() => {
  if (!routes.value.items.length) return 0
  const sum = routes.value.items.reduce(
    (acc, route) => acc + route.total_time_hours,
    0
  )
  return (sum / routes.value.items.length).toFixed(1)
})

const averageCost = computed(() => {
  if (!routes.value.items.length) return 0
  const sum = routes.value.items.reduce(
    (acc, route) => acc + route.total_cost_rub,
    0
  )
  return Math.round(sum / routes.value.items.length)
})

// Sort functions
const sortRoutes = (routes: Route[]): Route[] => {
  return [...routes].sort((a, b) => {
    let aValue: any = a[routeSortField.value]
    let bValue: any = b[routeSortField.value]

    if (routeSortField.value === 'created_at') {
      aValue = new Date(aValue).getTime()
      bValue = new Date(bValue).getTime()
    }

    if (aValue < bValue) return routeSortDirection.value === 'asc' ? -1 : 1
    if (aValue > bValue) return routeSortDirection.value === 'asc' ? 1 : -1
    return 0
  })
}

const sortMetrics = (metrics: Metric[]): Metric[] => {
  return [...metrics].sort((a, b) => {
    if (metricsSortField.value === 'timestamp') {
      const aTime = new Date(a.timestamp).getTime()
      const bTime = new Date(b.timestamp).getTime()
      return metricsSortDirection.value === 'asc'
        ? aTime - bTime
        : bTime - aTime
    }

    if (
      metricsSortField.value === 'model' ||
      metricsSortField.value === 'route_id'
    ) {
      const aValue = a[metricsSortField.value]
      const bValue = b[metricsSortField.value]

      if (aValue < bValue) return metricsSortDirection.value === 'asc' ? -1 : 1
      if (aValue > bValue) return metricsSortDirection.value === 'asc' ? 1 : -1
      return 0
    }

    const aValue = a[metricsSortField.value] as number
    const bValue = b[metricsSortField.value] as number

    if (aValue < bValue) return metricsSortDirection.value === 'asc' ? -1 : 1
    if (aValue > bValue) return metricsSortDirection.value === 'asc' ? 1 : -1
    return 0
  })
}

// Handlers
const handleRouteSort = (field: RouteSortField, direction: SortDirection) => {
  routeSortField.value = field
  routeSortDirection.value = direction
  routes.value = {
    total: routes.value.total,
    items: sortRoutes(routes.value.items)
  }
}

const handleMetricsSort = (
  field: MetricsSortField,
  direction: SortDirection
) => {
  metricsSortField.value = field
  metricsSortDirection.value = direction
  allMetrics.value = sortMetrics(allMetrics.value)
}

const handleRouteSelect = async (routeId: string) => {
  if (selectedRouteId.value === routeId) return

  selectedRouteId.value = routeId
  await loadRouteDetails(routeId)
}

// Data loading functions
const loadDashboardData = async () => {
  isLoadingStats.value = true
  isLoadingRoutes.value = true
  isLoadingComparison.value = true
  error.value = null

  // Загружаем данные независимо — ошибка одного не блокирует остальные
  const [routesResult, comparisonResult, healthResult] = await Promise.allSettled([
    fetchRoutes(0, 100),
    compareModels(),
    checkHealth()
  ])

  if (routesResult.status === 'fulfilled') {
    const routesData = routesResult.value
    routes.value = {
      total: routesData.total,
      items: sortRoutes(routesData.items ?? [])
    }
    if ((routesData.items?.length ?? 0) > 0) {
      selectedRouteId.value = routesData.items[0].id
      await loadRouteDetails(routesData.items[0].id)
    }
  } else {
    error.value = routesResult.reason?.message || 'Не удалось загрузить данные'
    console.error('Routes loading error:', routesResult.reason)
  }

  if (comparisonResult.status === 'fulfilled') {
    modelComparison.value = comparisonResult.value
  } else {
    console.error('Comparison loading error:', comparisonResult.reason)
  }

  if (healthResult.status === 'fulfilled') {
    healthStatus.value = healthResult.value
  } else {
    console.error('Health check error:', healthResult.reason)
  }

  isLoadingStats.value = false
  isLoadingRoutes.value = false
  isLoadingComparison.value = false
}

const loadRouteDetails = async (routeId: string) => {
  if (!routeId) return

  try {
    isLoadingRouteDetails.value = true

    const [details, metricsData] = await Promise.all([
      fetchRouteDetails(routeId),
      getMetrics()
    ])

    selectedRouteDetails.value = details
    routeMetrics.value = (metricsData?.metrics ?? []).filter(
      (m) => m.route_id === routeId
    )
  } catch (err: any) {
    console.error(`Error loading route ${routeId} details:`, err)
  } finally {
    isLoadingRouteDetails.value = false
  }
}

const loadMetrics = async () => {
  try {
    isLoadingMetrics.value = true
    const metricsData = await getMetrics()
    allMetrics.value = sortMetrics(metricsData?.metrics ?? [])
  } catch (err: any) {
    console.error('Metrics loading error:', err)
  } finally {
    isLoadingMetrics.value = false
  }
}

const refreshAllData = async () => {
  isRefreshing.value = true
  await Promise.all([loadDashboardData(), loadMetrics()])
  isRefreshing.value = false
}

// Lifecycle
onMounted(() => {
  loadDashboardData()
  loadMetrics()
})
</script>
