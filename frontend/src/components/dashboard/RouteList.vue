<template>
  <div class="overflow-hidden">
    <!-- Desktop Table -->
    <div class="hidden sm:block">
      <div class="align-middle inline-block min-w-full">
        <div class="overflow-hidden border border-gray-200 rounded-lg">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th
                  scope="col"
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  Маршрут
                </th>
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
                  Расстояние
                </th>
                <th
                  scope="col"
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  Время
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
              <tr
                v-for="route in routes"
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
      </div>
    </div>

    <!-- Mobile Cards -->
    <div class="sm:hidden space-y-3">
      <div
        v-for="route in routes"
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

    <!-- Empty State -->
    <div v-if="routes.length === 0" class="text-center py-8">
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
import type { Route } from '@/services/api'

defineProps<{
  routes: Route[]
  selectedRouteId?: string | null
}>()

defineEmits<{
  'select-route': [routeId: string]
}>()

const getModelName = (model: string): string => {
  const modelMap: Record<string, string> = {
    llama: 'Llama',
    qwen: 'Qwen',
    cotype: 'Cotype',
    tpro: 'T-Pro'
  }
  return modelMap[model] || model
}

const getModelInitial = (model: string): string => {
  const initialMap: Record<string, string> = {
    llama: 'L',
    qwen: 'Q',
    tpro: 'T'
  }
  return initialMap[model] || '?'
}

const getModelColor = (model: string): string => {
  const colorMap: Record<string, string> = {
    llama: 'bg-blue-500',
    qwen: 'bg-purple-500',
    tpro: 'bg-yellow-500'
  }
  return colorMap[model] || 'bg-gray-500'
}

const getModelBadgeClass = (model: string): string => {
  const badgeMap: Record<string, string> = {
    llama: 'bg-blue-100 text-blue-800',
    qwen: 'bg-purple-100 text-purple-800',
    tpro: 'bg-yellow-100 text-yellow-800'
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
