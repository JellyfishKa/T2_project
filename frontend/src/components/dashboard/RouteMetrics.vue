<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <template v-if="isLoading">
      <SkeletonLoader height="120px" />
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <SkeletonLoader v-for="i in 3" :key="i" height="100px" />
      </div>
      <SkeletonLoader height="200px" />
    </template>

    <!-- Selected Route Info -->
    <div v-else-if="route" class="bg-gray-50 rounded-lg p-4">
      <div class="flex items-center justify-between">
        <div>
          <h4 class="text-lg font-semibold text-gray-900">{{ route.name }}</h4>
          <p class="text-sm text-gray-600">ID: {{ route.id }}</p>
        </div>
        <div class="text-right">
          <span
            class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
            :class="getModelBadgeClass(route.model_used)"
          >
            {{ getModelName(route.model_used) }}
          </span>
          <p class="mt-1 text-sm text-gray-600">
            {{ formatDate(route.created_at) }}
          </p>
        </div>
      </div>
    </div>

    <!-- Key Metrics -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
      <MetricCard
        title="Общее расстояние"
        :value="route?.total_distance_km || 0"
        unit="км"
        color="blue"
        :loading="isLoading"
      />

      <MetricCard
        title="Общее время"
        :value="route?.total_time_hours || 0"
        unit="часов"
        color="green"
        :loading="isLoading"
      />

      <MetricCard
        title="Общая стоимость"
        :value="route?.total_cost_rub || 0"
        unit="₽"
        color="purple"
        :loading="isLoading"
      />
    </div>

    <!-- Model Performance Metrics -->
    <div
      v-if="metrics.length > 0 && !isLoading"
      class="border-t border-gray-200 pt-6"
    >
      <h5 class="text-lg font-medium text-gray-900 mb-4">
        Производительность моделей для этого маршрута
      </h5>

      <div class="overflow-hidden border border-gray-200 rounded-lg">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Модель
              </th>
              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Время ответа
              </th>
              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Качество
              </th>
              <th
                scope="col"
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Стоимость
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="metric in metrics" :key="metric.id">
              <td class="px-4 py-4 whitespace-nowrap">
                <span
                  class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                  :class="getModelBadgeClass(metric.model)"
                >
                  {{ getModelName(metric.model) }}
                </span>
              </td>
              <td class="px-4 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="w-24 bg-gray-200 rounded-full h-2.5">
                    <div
                      class="h-2.5 rounded-full"
                      :class="getResponseTimeColor(metric.response_time_ms)"
                      :style="{
                        width:
                          getResponseTimePercentage(metric.response_time_ms) +
                          '%'
                      }"
                    ></div>
                  </div>
                  <span class="ml-3 text-sm text-gray-900"
                    >{{ metric.response_time_ms }} мс</span
                  >
                </div>
              </td>
              <td class="px-4 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="w-24 bg-gray-200 rounded-full h-2.5">
                    <div
                      class="bg-green-600 h-2.5 rounded-full"
                      :style="{ width: metric.quality_score * 100 + '%' }"
                    ></div>
                  </div>
                  <span class="ml-3 text-sm text-gray-900"
                    >{{ (metric.quality_score * 100).toFixed(1) }}%</span
                  >
                </div>
              </td>
              <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ metric.cost_rub.toFixed(2) }} ₽
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="!route && !isLoading"
      class="text-center py-8 border rounded-lg border-gray-200"
    >
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">Нет данных</h3>
      <p class="mt-1 text-sm text-gray-500">
        Выберите маршрут для просмотра метрик
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import MetricCard from './MetricCard.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import type { RouteDetails, Metric } from '@/services/api'

defineProps<{
  route?: RouteDetails | null
  metrics: Metric[]
  isLoading?: boolean
}>()

const getModelName = (model: string): string => {
  const modelMap: Record<string, string> = {
    llama: 'Llama',
    qwen: 'Qwen',
    deepseek: 'DeepSeek'
  }
  return modelMap[model] || model
}

const getModelBadgeClass = (model: string): string => {
  const badgeMap: Record<string, string> = {
    llama: 'bg-blue-100 text-blue-800',
    qwen: 'bg-purple-100 text-purple-800',
    deepseek: 'bg-yellow-100 text-yellow-800'
  }
  return badgeMap[model] || 'bg-gray-100 text-gray-800'
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

const getResponseTimeColor = (responseTime: number): string => {
  if (responseTime < 800) return 'bg-green-500'
  if (responseTime < 1500) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getResponseTimePercentage = (responseTime: number): number => {
  return Math.min((responseTime / 2000) * 100, 100)
}
</script>
