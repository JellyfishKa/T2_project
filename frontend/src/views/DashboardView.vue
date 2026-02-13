<template>
  <div class="py-6 md:py-8">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-2xl md:text-3xl font-bold text-gray-900">Dashboard</h1>
      <p class="mt-2 text-gray-600">
        Обзор оптимизированных маршрутов и сравнение производительности моделей
      </p>
    </div>

    <!-- Health Status -->
    <div v-if="healthStatus" class="mb-6">
      <HealthStatus :status="healthStatus" />
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-12">
      <div
        class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"
      ></div>
      <p class="mt-4 text-gray-600">Загрузка данных...</p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
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

    <!-- Main Dashboard Content -->
    <div v-else class="space-y-6">
      <!-- Route Statistics -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
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

        <div
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

        <div
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
                @select-route="handleRouteSelect"
                :selected-route-id="selectedRouteId"
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
                :benchmark-results="benchmarkResults"
                :is-loading="isLoadingBenchmark"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Metrics -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200">
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
              class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Обновить
            </button>
          </div>
        </div>
        <div class="px-4 py-5 sm:p-6">
          <MetricsTable :metrics="allMetrics" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import RouteList from '@/components/dashboard/RouteList.vue'
import RouteMetrics from '@/components/dashboard/RouteMetrics.vue'
import ModelComparison from '@/components/dashboard/ModelComparison.vue'
import MetricsTable from '@/components/dashboard/MetricsTable.vue'
import HealthStatus from '@/components/dashboard/HealthStatus.vue'
import {
  fetchRoutes,
  fetchRouteDetails,
  getMetrics,
  runBenchmark,
  checkHealth,
  fetchAllLocations,
  type Route,
  type RouteDetails,
  type Metric,
  type BenchmarkResult,
  type HealthStatus as HealthStatusType
} from '@/services/api'

// State
const isLoading = ref(true)
const isLoadingBenchmark = ref(false)
const error = ref<string | null>(null)
const routes = ref<{ total: number; items: Route[] }>({ total: 0, items: [] })
const selectedRouteId = ref<string | null>(null)
const selectedRouteDetails = ref<RouteDetails | null>(null)
const routeMetrics = ref<Metric[]>([])
const allMetrics = ref<Metric[]>([])
const benchmarkResults = ref<BenchmarkResult[]>([])
const healthStatus = ref<HealthStatusType | null>(null)

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

// Methods
const loadDashboardData = async () => {
  try {
    isLoading.value = true
    error.value = null

    // Загружаем данные параллельно для скорости
    const [routesData, metricsData, healthData] = await Promise.all([
      fetchRoutes(),
      getMetrics(),
      checkHealth()
    ])

    routes.value = routesData
    allMetrics.value = metricsData.metrics
    healthStatus.value = healthData

    // Выбираем первый маршрут по умолчанию
    if (routesData.items.length > 0) {
      selectedRouteId.value = routesData.items[0].id
      await loadRouteDetails(routesData.items[0].id)
    }
  } catch (err: any) {
    error.value = err.message || 'Не удалось загрузить данные'
    console.error('Dashboard data loading error:', err)
  } finally {
    isLoading.value = false
  }
}

const loadRouteDetails = async (routeId: string) => {
  try {
    selectedRouteId.value = routeId

    // Загружаем детали маршрута и метрики параллельно
    const [details, metrics] = await Promise.all([
      fetchRouteDetails(routeId),
      getMetrics()
    ])

    selectedRouteDetails.value = details
    routeMetrics.value = metrics.metrics
  } catch (err: any) {
    console.error(`Error loading route ${routeId} details:`, err)
  }
}

const loadBenchmark = async () => {
  try {
    isLoadingBenchmark.value = true

    // Используем существующие локации для бенчмарка
    const locations = await fetchAllLocations()
    const testLocations = locations.slice(0, 3).map((loc) => ({
      id: loc.id,
      name: loc.name,
      latitude: loc.latitude,
      longitude: loc.longitude
    }))

    const benchmarkResult = await runBenchmark({
      test_locations: testLocations,
      num_iterations: 3
    })

    benchmarkResults.value = benchmarkResult.results
  } catch (err: any) {
    console.error('Benchmark loading error:', err)
  } finally {
    isLoadingBenchmark.value = false
  }
}

const loadMetrics = async () => {
  try {
    const metricsData = await getMetrics()
    allMetrics.value = metricsData.metrics
  } catch (err: any) {
    console.error('Metrics loading error:', err)
  }
}

const handleRouteSelect = (routeId: string) => {
  loadRouteDetails(routeId)
}

// Lifecycle
onMounted(() => {
  loadDashboardData()
  loadBenchmark()
})
</script>
