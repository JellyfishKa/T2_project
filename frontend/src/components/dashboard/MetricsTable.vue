<template>
  <div class="overflow-hidden">
    <!-- Loading State -->
    <div v-if="isLoading" class="space-y-3">
      <SkeletonLoader v-for="i in 5" :key="i" height="60px" />
    </div>

    <!-- Desktop Table (only shown when not loading and has data) -->
    <div v-else-if="metrics.length > 0" class="hidden sm:block overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.field"
              scope="col"
              class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
              @click="handleSort(column.field)"
            >
              <div class="flex items-center space-x-1">
                <span>{{ column.label }}</span>
                <span
                  v-if="sortable && sortField === column.field"
                  class="text-gray-400"
                >
                  {{ sortDirection === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="metric in sortedMetrics" :key="metric.id">
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

    <!-- Mobile Cards (only shown when not loading and has data) -->
    <div v-else-if="metrics.length > 0" class="sm:hidden space-y-3">
      <div
        v-for="metric in sortedMetrics"
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

    <!-- Empty State (only shown when not loading and no data) -->
    <div v-else class="text-center py-8">
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
import { computed } from 'vue'
import type { Metric } from '@/services/api'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'

type SortField =
  | 'model'
  | 'route_id'
  | 'response_time_ms'
  | 'quality_score'
  | 'cost_rub'
  | 'timestamp'
type SortDirection = 'asc' | 'desc'

const props = defineProps<{
  metrics: Metric[]
  isLoading?: boolean
  sortable?: boolean
  sortField?: SortField
  sortDirection?: SortDirection
}>()

const emit = defineEmits<{
  (e: 'sort', field: SortField, direction: SortDirection): void
}>()

const columns = [
  { field: 'model' as const, label: 'Модель' },
  { field: 'route_id' as const, label: 'Маршрут' },
  { field: 'response_time_ms' as const, label: 'Время ответа' },
  { field: 'quality_score' as const, label: 'Качество' },
  { field: 'cost_rub' as const, label: 'Стоимость' },
  { field: 'timestamp' as const, label: 'Время' }
]

const sortedMetrics = computed(() => {
  if (!props.sortable || !props.sortField) return props.metrics

  return [...props.metrics].sort((a, b) => {
    const sortField = props.sortField as SortField

    if (sortField === 'timestamp') {
      const aTime = new Date(a.timestamp).getTime()
      const bTime = new Date(b.timestamp).getTime()
      return props.sortDirection === 'asc' ? aTime - bTime : bTime - aTime
    }

    if (sortField === 'model' || sortField === 'route_id') {
      const aValue = a[sortField]
      const bValue = b[sortField]

      if (aValue < bValue) return props.sortDirection === 'asc' ? -1 : 1
      if (aValue > bValue) return props.sortDirection === 'asc' ? 1 : -1
      return 0
    }

    // Для числовых полей
    const aValue = a[sortField] as number
    const bValue = b[sortField] as number

    if (aValue < bValue) return props.sortDirection === 'asc' ? -1 : 1
    if (aValue > bValue) return props.sortDirection === 'asc' ? 1 : -1
    return 0
  })
})

const handleSort = (field: SortField) => {
  if (!props.sortable) return

  const direction =
    props.sortField === field && props.sortDirection === 'asc' ? 'desc' : 'asc'
  emit('sort', field, direction)
}

// Helper functions
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
