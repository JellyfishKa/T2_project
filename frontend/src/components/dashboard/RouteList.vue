<template>
  <div class="overflow-hidden">
    <!-- Loading State -->
    <div v-if="isLoading" class="space-y-3">
      <SkeletonLoader v-for="i in 5" :key="i" height="80px" />
    </div>

    <!-- Desktop Table (only shown when not loading and has data) -->
    <div v-else-if="routes.length > 0" class="hidden sm:block overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              v-for="column in columns"
              :key="column.field"
              scope="col"
              class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
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
          <tr
            v-for="route in sortedRoutes"
            :key="route.id"
            @click="$emit('select-route', route.id)"
            :class="[
              'cursor-pointer hover:bg-gray-50 transition-colors duration-150',
              selectedRouteId === route.id ? 'bg-blue-50' : ''
            ]"
          >
            <td class="px-4 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <div class="flex-shrink-0 h-10 w-10">
                  <div
                    class="h-10 w-10 rounded-lg flex items-center justify-center"
                    :class="getModelColor(route.model_used)"
                  >
                    <span class="text-white font-bold text-sm">{{
                      getModelInitial(route.model_used)
                    }}</span>
                  </div>
                </div>
                <div class="ml-4">
                  <div class="text-sm font-medium text-gray-900">
                    {{ route.name }}
                  </div>
                  <div class="text-sm text-gray-500">
                    {{ formatDate(route.created_at) }}
                  </div>
                </div>
              </div>
            </td>
            <td class="px-4 py-4 whitespace-nowrap">
              <span
                class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                :class="getModelBadgeClass(route.model_used)"
              >
                {{ getModelName(route.model_used) }}
              </span>
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
              {{ route.total_distance_km.toFixed(1) }} км
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
              {{ route.total_time_hours.toFixed(1) }} ч
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
              {{ route.total_cost_rub.toFixed(0) }} ₽
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile Cards (only shown when not loading and has data) -->
    <div v-else-if="routes.length > 0" class="sm:hidden space-y-3">
      <div
        v-for="route in sortedRoutes"
        :key="route.id"
        @click="$emit('select-route', route.id)"
        :class="[
          'bg-white border rounded-lg p-4 cursor-pointer hover:border-gray-300 transition-colors duration-150',
          selectedRouteId === route.id
            ? 'border-blue-300 bg-blue-50'
            : 'border-gray-200'
        ]"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center">
            <div
              class="h-10 w-10 rounded-lg flex items-center justify-center"
              :class="getModelColor(route.model_used)"
            >
              <span class="text-white font-bold text-sm">{{
                getModelInitial(route.model_used)
              }}</span>
            </div>
            <div class="ml-3">
              <div class="text-sm font-medium text-gray-900">
                {{ route.name }}
              </div>
              <div class="text-xs text-gray-500">
                {{ getModelName(route.model_used) }}
              </div>
            </div>
          </div>
          <span
            class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
            :class="getModelBadgeClass(route.model_used)"
          >
            {{ getModelName(route.model_used) }}
          </span>
        </div>

        <div class="mt-4 grid grid-cols-3 gap-2">
          <div class="text-center">
            <div class="text-sm font-medium text-gray-900">
              {{ route.total_distance_km.toFixed(1) }} км
            </div>
            <div class="text-xs text-gray-500">Расстояние</div>
          </div>
          <div class="text-center">
            <div class="text-sm font-medium text-gray-900">
              {{ route.total_time_hours.toFixed(1) }} ч
            </div>
            <div class="text-xs text-gray-500">Время</div>
          </div>
          <div class="text-center">
            <div class="text-sm font-medium text-gray-900">
              {{ route.total_cost_rub.toFixed(0) }} ₽
            </div>
            <div class="text-xs text-gray-500">Стоимость</div>
          </div>
        </div>

        <div class="mt-3 text-xs text-gray-500">
          Создан: {{ formatDate(route.created_at) }}
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
          d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
        />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">Нет маршрутов</h3>
      <p class="mt-1 text-sm text-gray-500">
        Создайте первый маршрут в разделе Optimize
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Route } from '@/services/api'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'

type SortField =
  | 'created_at'
  | 'total_distance_km'
  | 'total_time_hours'
  | 'total_cost_rub'
  | 'model_used'
  | 'name'
type SortDirection = 'asc' | 'desc'

const props = defineProps<{
  routes: Route[]
  isLoading?: boolean
  selectedRouteId?: string | null
  sortable?: boolean
  sortField?: SortField
  sortDirection?: SortDirection
}>()

const emit = defineEmits<{
  (e: 'select-route', routeId: string): void
  (e: 'sort', field: SortField, direction: SortDirection): void
}>()

const columns = [
  { field: 'name' as const, label: 'Маршрут' },
  { field: 'model_used' as const, label: 'Модель' },
  { field: 'total_distance_km' as const, label: 'Расстояние' },
  { field: 'total_time_hours' as const, label: 'Время' },
  { field: 'total_cost_rub' as const, label: 'Стоимость' }
]

const sortedRoutes = computed(() => {
  if (!props.sortable || !props.sortField) return props.routes

  return [...props.routes].sort((a, b) => {
    let aValue: any = a[props.sortField!]
    let bValue: any = b[props.sortField!]

    if (props.sortField === 'created_at') {
      aValue = new Date(aValue).getTime()
      bValue = new Date(bValue).getTime()
    }

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

const getModelInitial = (model: string): string => {
  const initialMap: Record<string, string> = {
    llama: 'L',
    qwen: 'Q'
  }
  return initialMap[model] || '?'
}

const getModelColor = (model: string): string => {
  const colorMap: Record<string, string> = {
    llama: 'bg-blue-300',
    qwen: 'bg-purple-500'
  }
  return colorMap[model] || 'bg-gray-500'
}

const getModelBadgeClass = (model: string): string => {
  const badgeMap: Record<string, string> = {
    llama: 'bg-blue-100 text-blue-800',
    qwen: 'bg-purple-100 text-purple-800'
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
</script>
