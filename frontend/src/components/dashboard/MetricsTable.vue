<template>
  <div class="overflow-hidden">
    <!-- Desktop Table -->
    <div class="hidden sm:block overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th
              scope="col"
              class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Модель
            </th>
            <th
              scope="col"
              class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Маршрут
            </th>
            <th
              scope="col"
              class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Время ответа
            </th>
            <th
              scope="col"
              class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Качество
            </th>
            <th
              scope="col"
              class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Стоимость
            </th>
            <th
              scope="col"
              class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Время
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="metric in metrics" :key="metric.id">
            <td class="px-3 py-4 whitespace-nowrap">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="getModelBadgeClass(metric.model)"
              >
                {{ getModelName(metric.model) }}
              </span>
            </td>
            <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-900">
              {{ metric.route_id }}
            </td>
            <td class="px-3 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <div class="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    class="h-2 rounded-full"
                    :class="getResponseTimeColor(metric.response_time_ms)"
                    :style="{
                      width:
                        getResponseTimePercentage(metric.response_time_ms) + '%'
                    }"
                  ></div>
                </div>
                <span class="ml-3 text-sm text-gray-900"
                  >{{ metric.response_time_ms }} мс</span
                >
              </div>
            </td>
            <td class="px-3 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <div class="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-green-500 h-2 rounded-full"
                    :style="{ width: metric.quality_score * 100 + '%' }"
                  ></div>
                </div>
                <span class="ml-3 text-sm text-gray-900"
                  >{{ (metric.quality_score * 100).toFixed(1) }}%</span
                >
              </div>
            </td>
            <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-900">
              {{ metric.cost_rub.toFixed(2) }} ₽
            </td>
            <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatTime(metric.timestamp) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile Cards -->
    <div class="sm:hidden space-y-3">
      <div
        v-for="metric in metrics"
        :key="metric.id"
        class="bg-white border border-gray-200 rounded-lg p-4"
      >
        <div class="flex items-center justify-between mb-3">
          <span
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
            :class="getModelBadgeClass(metric.model)"
          >
            {{ getModelName(metric.model) }}
          </span>
          <span class="text-xs text-gray-500">{{
            formatTime(metric.timestamp)
          }}</span>
        </div>

        <div class="space-y-2">
          <div class="flex justify-between">
            <span class="text-sm text-gray-600">Маршрут:</span>
            <span class="text-sm font-medium text-gray-900">{{
              metric.route_id
            }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-600">Время ответа:</span>
            <span class="text-sm font-medium text-gray-900"
              >{{ metric.response_time_ms }} мс</span
            >
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-600">Качество:</span>
            <span class="text-sm font-medium text-gray-900"
              >{{ (metric.quality_score * 100).toFixed(1) }}%</span
            >
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-600">Стоимость:</span>
            <span class="text-sm font-medium text-gray-900"
              >{{ metric.cost_rub.toFixed(2) }} ₽</span
            >
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="metrics.length === 0" class="text-center py-8">
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
      <h3 class="mt-2 text-sm font-medium text-gray-900">Нет метрик</h3>
      <p class="mt-1 text-sm text-gray-500">
        Запустите оптимизацию для создания метрик
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Metric } from '@/services/api'

defineProps<{
  metrics: Metric[]
}>()

const getModelName = (model: string): string => {
  const modelMap: Record<string, string> = {
    llama: 'Llama',
    qwen: 'Qwen',
    tpro: 'T-Pro'
  }
  return modelMap[model] || model
}

const getModelBadgeClass = (model: string): string => {
  const badgeMap: Record<string, string> = {
    gigachat: 'bg-green-100 text-green-800',
    qwen: 'bg-purple-100 text-purple-800',
    cotype: 'bg-blue-100 text-blue-800',
    tpro: 'bg-yellow-100 text-yellow-800'
  }
  return badgeMap[model] || 'bg-gray-100 text-gray-800'
}

const getResponseTimeColor = (responseTime: number): string => {
  if (responseTime < 800) return 'bg-green-500'
  if (responseTime < 1500) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getResponseTimePercentage = (responseTime: number): number => {
  return Math.min((responseTime / 2000) * 100, 100)
}

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  return new Intl.DateTimeFormat('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}
</script>
