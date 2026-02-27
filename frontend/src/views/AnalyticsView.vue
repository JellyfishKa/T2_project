<template>
  <div class="py-6 md:py-8">
    <!-- Page Header -->
    <div
      class="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900">Аналитика</h1>
        <p class="mt-2 text-gray-600">
          Статистика и визуализация производительности маршрутов и моделей
        </p>
      </div>
      <button
        @click="refreshData"
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
        {{ isRefreshing ? 'Обновление...' : 'Обновить' }}
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
            @click="loadAnalyticsData"
            class="mt-3 text-sm font-medium text-red-800 hover:text-red-900"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Statistics Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <!-- Total Routes -->
        <div
          v-if="!isLoading"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
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
                {{ stats.totalRoutes }}
              </p>
            </div>
          </div>
        </div>
        <SkeletonLoader v-else height="120px" />

        <!-- Average Distance -->
        <div
          v-if="!isLoading"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
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
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">
                Среднее расстояние
              </p>
              <p class="text-2xl font-semibold text-gray-900">
                {{ stats.avgDistance.toFixed(1) }} км
              </p>
            </div>
          </div>
        </div>
        <SkeletonLoader v-else height="120px" />

        <!-- Average Cost -->
        <div
          v-if="!isLoading"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
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
                {{ stats.avgCost.toFixed(0) }} ₽
              </p>
            </div>
          </div>
        </div>
        <SkeletonLoader v-else height="120px" />

        <!-- Avg Quality -->
        <div
          v-if="!isLoading"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
        >
          <div class="flex items-center">
            <div class="flex-shrink-0 bg-yellow-100 rounded-lg p-3">
              <svg
                class="h-6 w-6 text-yellow-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">Среднее качество</p>
              <p class="text-2xl font-semibold text-gray-900">
                {{ stats.avgQuality.toFixed(1) }}%
              </p>
            </div>
          </div>
        </div>
        <SkeletonLoader v-else height="120px" />
      </div>

      <!-- Charts Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <!-- Model Performance Chart (Bar Chart) -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            Производительность моделей
          </h3>
          <p class="text-sm text-gray-600 mb-4">
            Среднее время ответа по моделям (мс)
          </p>
          <div v-if="isLoading" class="h-64 flex items-center justify-center">
            <SkeletonLoader height="200px" />
          </div>
          <div v-else-if="modelPerformanceData.labels.length" class="h-64">
            <BarChart
              :data="modelPerformanceData"
              :options="barChartOptions"
            />
          </div>
          <div
            v-else
            class="h-64 flex items-center justify-center text-gray-500"
          >
            Нет данных для отображения
          </div>
        </div>

        <!-- Distance vs Cost Chart (Scatter Plot) -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            Расстояние vs Стоимость
          </h3>
          <p class="text-sm text-gray-600 mb-4">
            Корреляция между расстоянием и стоимостью
          </p>
          <div v-if="isLoading" class="h-64 flex items-center justify-center">
            <SkeletonLoader height="200px" />
          </div>
          <div v-else-if="scatterData.datasets[0]?.data.length" class="h-64">
            <ScatterChart
              :data="scatterData"
              :options="scatterChartOptions"
            />
          </div>
          <div
            v-else
            class="h-64 flex items-center justify-center text-gray-500"
          >
            Нет данных для отображения
          </div>
        </div>
      </div>

      <!-- Time Series Chart (Line Chart) -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          Динамика оптимизации
        </h3>
        <p class="text-sm text-gray-600 mb-4">
          Оценка качества решений во времени
        </p>
        <div v-if="isLoading" class="h-80 flex items-center justify-center">
          <SkeletonLoader height="300px" />
        </div>
        <div v-else-if="timeSeriesData.labels.length" class="h-80">
            <LineChart
            :data="timeSeriesData"
            :options="lineChartOptions"
          />
        </div>
        <div v-else class="h-80 flex items-center justify-center text-gray-500">
          Нет данных для отображения
        </div>
      </div>

      <!-- Additional Stats Table -->
      <div
        class="mt-6 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
      >
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">
            Детальная статистика по моделям
          </h3>
        </div>
        <div class="p-6">
          <div v-if="isLoading" class="space-y-3">
            <SkeletonLoader v-for="i in 3" :key="i" height="60px" />
          </div>
          <div v-else-if="modelStats.length" class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                  >
                    Модель
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                  >
                    Использовано
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                  >
                    Ср. время (мс)
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                  >
                    Ср. качество
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                  >
                    Общая стоимость
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                <tr v-for="stat in modelStats" :key="stat.model">
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getModelBadgeClass(stat.model)"
                    >
                      {{ getModelName(stat.model) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {{ stat.count }}
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {{ stat.avgResponseTime.toFixed(0) }}
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {{ stat.avgQuality.toFixed(1) }}%
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {{ stat.totalCost.toFixed(2) }} ₽
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="text-center py-8 text-gray-500">
            Нет данных по моделям
          </div>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════════
           РАЗДЕЛ: Охват торговых точек (из /insights)
      ════════════════════════════════════════════════════════════════════ -->
      <div v-if="insights" class="mt-8">
        <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 class="text-xl font-semibold text-gray-900">
            Охват торговых точек — {{ insights.month }}
          </h2>
          <div class="flex items-center gap-2">
            <!-- Импорт заполненного Excel -->
            <label
              class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg cursor-pointer disabled:opacity-50 transition-colors"
              :class="{ 'opacity-50 pointer-events-none': importLoading }"
              title="Загрузить заполненный Excel с результатами визитов"
            >
              <svg v-if="importLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4 0l4-4m0 0l4 4m-4-4v12"/>
              </svg>
              {{ importLoading ? 'Импорт…' : 'Загрузить Excel' }}
              <input
                type="file"
                accept=".xlsx,.xls"
                class="hidden"
                :disabled="importLoading"
                @change="handleImport"
              />
            </label>

            <!-- Экспорт -->
            <button
              @click="handleExport"
              :disabled="exportLoading"
              class="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
            >
              <svg v-if="exportLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
              {{ exportLoading ? 'Экспорт…' : 'Скачать Excel' }}
            </button>
          </div>
        </div>

        <!-- Результат импорта -->
        <div v-if="importResult" class="mb-4 rounded-lg border p-3 text-sm"
          :class="importResult.errors.length && !importResult.updated
            ? 'bg-red-50 border-red-200 text-red-700'
            : 'bg-green-50 border-green-200 text-green-800'"
        >
          <p class="font-medium">
            Импорт завершён: обновлено {{ importResult.updated }}, пропущено {{ importResult.skipped }}
          </p>
          <ul v-if="importResult.errors.length" class="mt-1 space-y-0.5 text-xs opacity-80">
            <li v-for="e in importResult.errors" :key="e">• {{ e }}</li>
          </ul>
        </div>

        <!-- Сводные карточки -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Всего ТТ</p>
            <p class="text-3xl font-bold text-gray-900 mt-1">{{ insights.total_tt }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Охват</p>
            <p class="text-3xl font-bold mt-1" :class="insights.coverage_pct >= 80 ? 'text-green-600' : 'text-amber-500'">
              {{ insights.coverage_pct }}%
            </p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Запланировано</p>
            <p class="text-3xl font-bold text-blue-600 mt-1">{{ insights.visits_this_month.planned }}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Выполнено</p>
            <p class="text-3xl font-bold text-green-600 mt-1">{{ insights.visits_this_month.completed }}</p>
            <p class="text-xs text-gray-400 mt-0.5">{{ insights.visits_this_month.completion_rate }}% выполнения</p>
          </div>
        </div>

        <!-- По категориям -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 class="text-sm font-semibold text-gray-700 mb-4">Выполнение по категориям ТТ</h3>
            <div class="space-y-3">
              <div
                v-for="(cat, key) in insights.by_category"
                :key="key"
                class="flex items-center gap-3"
              >
                <span
                  class="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                  :class="{
                    'bg-red-500': key === 'A',
                    'bg-orange-500': key === 'B',
                    'bg-yellow-500': key === 'C',
                    'bg-gray-400': key === 'D',
                  }"
                >{{ key }}</span>
                <div class="flex-1">
                  <div class="flex justify-between text-xs text-gray-500 mb-1">
                    <span>{{ cat.completed }} / {{ cat.planned }} визитов</span>
                    <span class="font-medium" :class="cat.pct >= 80 ? 'text-green-600' : 'text-gray-500'">
                      {{ cat.pct }}%
                    </span>
                  </div>
                  <div class="w-full bg-gray-100 rounded-full h-2">
                    <div
                      class="h-2 rounded-full transition-all"
                      :class="{
                        'bg-red-500': key === 'A',
                        'bg-orange-500': key === 'B',
                        'bg-yellow-400': key === 'C',
                        'bg-gray-400': key === 'D',
                      }"
                      :style="{ width: `${Math.max(cat.pct, 1)}%` }"
                    />
                  </div>
                </div>
                <span class="text-xs text-gray-400 w-12 text-right">{{ cat.total }} ТТ</span>
              </div>
            </div>
          </div>

          <!-- Активность торговых представителей -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 class="text-sm font-semibold text-gray-700 mb-4">Активность торговых представителей</h3>
            <div class="space-y-2">
              <div
                v-for="rep in insights.rep_activity"
                :key="rep.rep_id"
                class="flex items-center justify-between py-2 border-b border-gray-50 last:border-0"
              >
                <div>
                  <p class="text-sm font-medium text-gray-900">{{ rep.rep_name }}</p>
                  <p class="text-xs text-gray-400">{{ rep.outings_count }} выходов на маршрут</p>
                </div>
                <div class="text-right">
                  <p class="text-sm font-bold text-blue-600">{{ rep.tt_visited }}</p>
                  <p class="text-xs text-gray-400">ТТ посещено</p>
                </div>
              </div>
              <div v-if="!insights.rep_activity?.length" class="text-center py-4 text-gray-400 text-sm">
                Нет данных за этот месяц
              </div>
            </div>
          </div>
        </div>

        <!-- По районам -->
        <div v-if="insights.by_district?.length" class="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h3 class="text-sm font-semibold text-gray-700 mb-4">Охват по районам</h3>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            <div
              v-for="d in insights.by_district"
              :key="d.district"
              class="text-center p-3 bg-gray-50 rounded-lg"
            >
              <p class="text-xs font-medium text-gray-700 truncate">{{ d.district || 'Не указан' }}</p>
              <p class="text-lg font-bold mt-1" :class="d.coverage_pct >= 80 ? 'text-green-600' : 'text-amber-500'">
                {{ d.coverage_pct }}%
              </p>
              <p class="text-xs text-gray-400">{{ d.total }} ТТ</p>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler
} from 'chart.js'
import { Bar as BarChart, Scatter as ScatterChart, Line as LineChart } from 'vue-chartjs'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import {
  fetchRoutes,
  getMetrics,
  compareModels,
  getInsights,
  downloadScheduleExcel,
  importScheduleExcel,
  type Route,
  type Metric
} from '@/services/api'
import type { Insights } from '@/services/types'

// Register ChartJS components
ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler
)

// Types
interface ModelStat {
  model: string
  count: number
  avgResponseTime: number
  avgQuality: number
  totalCost: number
}

interface Stats {
  totalRoutes: number
  avgDistance: number
  avgCost: number
  avgQuality: number
}

// State
const isLoading = ref(true)
const isRefreshing = ref(false)
const error = ref<string | null>(null)

const routes = ref<Route[]>([])
const metrics = ref<Metric[]>([])
const modelComparison = ref<any>(null)
const insights = ref<Insights | null>(null)
const exportLoading = ref(false)
const importLoading = ref(false)
const importResult = ref<{ updated: number; skipped: number; errors: string[] } | null>(null)

// Текущий месяц для инсайтов
const insightsMonth = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
})

// Chart options
const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: (context: any) => `${context.raw} мс`
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: 'Время ответа (мс)'
      }
    }
  }
}

const scatterChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    tooltip: {
      callbacks: {
        label: (context: any) => {
          return [
            `Расстояние: ${context.raw.x.toFixed(1)} км`,
            `Стоимость: ${context.raw.y.toFixed(0)} ₽`,
            `Маршрут: ${context.raw.routeName}`
          ]
        }
      }
    },
    legend: {
      display: false
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: 'Расстояние (км)'
      }
    },
    y: {
      title: {
        display: true,
        text: 'Стоимость (₽)'
      }
    }
  }
}

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          return `${Number(context.raw).toFixed(1)}%`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: 'Качество решения (%)'
      },
      ticks: {
        callback: (value: any) => `${Number(value).toFixed(0)}%`
      }
    }
  }
}

// Computed
const stats = computed<Stats>(() => {
  if (!routes.value.length) {
    return {
      totalRoutes: 0,
      avgDistance: 0,
      avgCost: 0,
      avgQuality: 0
    }
  }

  const totalDistance = routes.value.reduce(
    (sum, r) => sum + (r.total_distance_km ?? 0),
    0
  )
  const totalCost = routes.value.reduce((sum, r) => sum + (r.total_cost_rub ?? 0), 0)
  const avgQuality = metrics.value.length
    ? metrics.value.reduce((sum, m) => sum + (m.quality_score ?? 0), 0) /
      metrics.value.length
    : 0

  return {
    totalRoutes: routes.value.length,
    avgDistance: totalDistance / routes.value.length,
    avgCost: totalCost / routes.value.length,
    avgQuality
  }
})

const modelStats = computed<ModelStat[]>(() => {
  if (!metrics.value.length) return []

  const statsMap = new Map<
    string,
    {
      count: number
      totalTime: number
      totalQuality: number
      totalCost: number
    }
  >()

  metrics.value.forEach((metric) => {
    const existing = statsMap.get(metric.model) || {
      count: 0,
      totalTime: 0,
      totalQuality: 0,
      totalCost: 0
    }

    statsMap.set(metric.model, {
      count: existing.count + 1,
      totalTime: existing.totalTime + metric.response_time_ms,
      totalQuality: existing.totalQuality + metric.quality_score,
      totalCost: existing.totalCost + metric.cost_rub
    })
  })

  return Array.from(statsMap.entries()).map(([model, data]) => ({
    model,
    count: data.count,
    avgResponseTime: data.totalTime / data.count,
    avgQuality: data.totalQuality / data.count,
    totalCost: data.totalCost
  }))
})

const modelPerformanceData = computed(() => {
  // Приоритет: данные сравнения моделей, иначе — агрегированные метрики
  const source: { label: string; value: number }[] =
    modelComparison.value?.models?.length
      ? modelComparison.value.models.map((m: any) => ({
          label: m.name as string,
          value: m.avg_response_time_ms as number
        }))
      : modelStats.value.map((m: ModelStat) => ({
          label: m.model,
          value: Math.round(m.avgResponseTime)
        }))

  if (!source.length) return { labels: [], datasets: [] }

  return {
    labels: source.map((m) => m.label),
    datasets: [
      {
        label: 'Время ответа (мс)',
        backgroundColor: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'],
        data: source.map((m) => m.value)
      }
    ]
  }
})

const scatterData = computed(() => {
  if (!routes.value.length) {
    return {
      datasets: [
        {
          label: 'Маршруты',
          data: [],
          backgroundColor: '#3b82f6'
        }
      ]
    }
  }

  return {
    datasets: [
      {
        label: 'Маршруты',
        data: routes.value.map((route) => ({
          x: route.total_distance_km,
          y: route.total_cost_rub,
          routeName: route.name
        })),
        backgroundColor: routes.value.map((route) => {
          switch (route.model_used) {
            case 'llama':
              return '#3b82f6'
            case 'qwen':
              return '#8b5cf6'
            default:
              return '#6b7280'
          }
        }),
        pointRadius: 6,
        pointHoverRadius: 8
      }
    ]
  }
})

const timeSeriesData = computed(() => {
  if (!routes.value.length) {
    return {
      labels: [],
      datasets: []
    }
  }

  // Sort routes by date
  const sortedRoutes = [...routes.value].sort(
    (a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )

  // Group metrics by route
  const routeMetrics = new Map<string, Metric[]>()
  metrics.value.forEach((metric) => {
    if (!routeMetrics.has(metric.route_id)) {
      routeMetrics.set(metric.route_id, [])
    }
    routeMetrics.get(metric.route_id)!.push(metric)
  })

  // Calculate average quality for each route
  const routeQuality = sortedRoutes.map((route) => {
    const routeMetricsList = routeMetrics.get(route.id) || []
    const avgQuality = routeMetricsList.length
      ? routeMetricsList.reduce((sum, m) => sum + m.quality_score, 0) /
        routeMetricsList.length
      : 0
    return {
      date: new Date(route.created_at).toLocaleDateString(),
      quality: avgQuality
    }
  })

  return {
    labels: routeQuality.map((r) => r.date),
    datasets: [
      {
        label: 'Качество решения',
        data: routeQuality.map((r) => r.quality),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  }
})

// Methods
const getModelName = (model: string): string => {
  const modelMap: Record<string, string> = {
    llama: 'Llama',
    qwen: 'Qwen'
  }
  return modelMap[model] || model
}

const getModelBadgeClass = (model: string): string => {
  const badgeMap: Record<string, string> = {
    llama: 'bg-blue-100 text-blue-800',
    qwen: 'bg-purple-100 text-purple-800'
  }
  return badgeMap[model] || 'bg-gray-100 text-gray-800'
}

const loadAnalyticsData = async () => {
  try {
    isLoading.value = true
    error.value = null

    const [routesData, metricsData, comparisonData, insightsData] = await Promise.all([
      fetchRoutes(0, 100),
      getMetrics(),
      compareModels().catch(() => null),  // /benchmark/compare может отсутствовать
      getInsights().catch(() => null),
    ])

    routes.value = routesData.items ?? []
    metrics.value = metricsData?.metrics ?? []
    modelComparison.value = comparisonData
    insights.value = insightsData
  } catch (err: any) {
    error.value = err.message || 'Не удалось загрузить данные аналитики'
    console.error('Analytics data loading error:', err)
  } finally {
    isLoading.value = false
  }
}

const handleExport = async () => {
  exportLoading.value = true
  try {
    await downloadScheduleExcel(insightsMonth.value)
  } catch (e: any) {
    alert('Ошибка экспорта: ' + (e?.message ?? 'неизвестная ошибка'))
  } finally {
    exportLoading.value = false
  }
}

const handleImport = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  importLoading.value = true
  importResult.value = null
  try {
    importResult.value = await importScheduleExcel(file)
    await loadAnalyticsData()
  } catch (e: any) {
    importResult.value = { updated: 0, skipped: 0, errors: [e?.message ?? 'неизвестная ошибка'] }
  } finally {
    importLoading.value = false
    target.value = ''
  }
}

const refreshData = async () => {
  isRefreshing.value = true
  await loadAnalyticsData()
  isRefreshing.value = false
}

// Lifecycle
onMounted(() => {
  loadAnalyticsData()
})
</script>
