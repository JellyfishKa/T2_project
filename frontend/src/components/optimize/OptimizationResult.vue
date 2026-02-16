<template>
  <div
    class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
  >
    <!-- Header with model info - показываем только если есть result -->
    <div
      v-if="result"
      class="px-6 py-5 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50"
    >
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">
            Результат оптимизации
          </h3>
          <p class="text-sm text-gray-600 mt-1">
            Маршрут оптимизирован с использованием
            <span class="font-medium text-blue-600">{{
              getModelName(result.model_used)
            }}</span>
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <span
            class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
            :class="getModelBadgeClass(result.model_used)"
          >
            {{ getModelName(result.model_used) }}
          </span>
          <button
            @click="$emit('reset')"
            class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            title="Новая оптимизация"
          >
            <svg
              class="h-5 w-5"
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
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="p-12 text-center">
      <div
        class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"
      ></div>
      <p class="mt-4 text-gray-600">Оптимизация маршрута...</p>
      <p class="text-sm text-gray-500">Это может занять несколько секунд</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-8 text-center">
      <div class="text-red-600 mb-4">
        <svg
          class="h-16 w-16 mx-auto"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
      </div>
      <h4 class="text-lg font-medium text-gray-900 mb-2">Ошибка оптимизации</h4>
      <p class="text-gray-600 mb-4">{{ error }}</p>
      <button
        @click="$emit('retry')"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700"
      >
        Попробовать снова
      </button>
    </div>

    <!-- Results -->
    <div v-else-if="result" class="divide-y divide-gray-200">
      <!-- Improvement Badge -->
      <div v-if="improvementPercentageNumber > 0" class="px-6 py-4 bg-green-50">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <svg
              class="h-5 w-5 text-green-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm font-medium text-green-800">
              Улучшение на {{ improvementPercentageString }}% по сравнению с
              исходным маршрутом
            </p>
          </div>
        </div>
      </div>

      <!-- Key Metrics -->
      <div class="px-6 py-5 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-gray-50 rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">Общее расстояние</p>
          <p class="text-2xl font-bold text-gray-900">
            {{ result.total_distance_km.toFixed(1) }} км
          </p>
          <p v-if="originalMetrics" class="text-xs text-gray-500 mt-1">
            Было: {{ originalMetrics.total_distance_km.toFixed(1) }} км
          </p>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">Общее время</p>
          <p class="text-2xl font-bold text-gray-900">
            {{ result.total_time_hours.toFixed(1) }} ч
          </p>
          <p v-if="originalMetrics" class="text-xs text-gray-500 mt-1">
            Было: {{ originalMetrics.total_time_hours.toFixed(1) }} ч
          </p>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">Общая стоимость</p>
          <p class="text-2xl font-bold text-gray-900">
            {{ result.total_cost_rub.toFixed(0) }} ₽
          </p>
          <p v-if="originalMetrics" class="text-xs text-gray-500 mt-1">
            Было: {{ originalMetrics.total_cost_rub.toFixed(0) }} ₽
          </p>
        </div>
      </div>

      <!-- Fallback Reason (if any) -->
      <div v-if="result.fallback_reason" class="px-6 py-3 bg-yellow-50">
        <div class="flex items-center">
          <svg
            class="h-5 w-5 text-yellow-400 mr-2"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          <span class="text-sm text-yellow-800">
            Использована резервная модель: {{ result.fallback_reason }}
          </span>
        </div>
      </div>

      <!-- Optimized Order -->
      <div class="px-6 py-5">
        <h4 class="text-sm font-medium text-gray-900 mb-4">
          Оптимизированный порядок посещения
        </h4>
        <div class="space-y-3">
          <div
            v-for="(locationId, index) in result.locations"
            :key="locationId"
            class="flex items-center"
          >
            <div
              class="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3"
            >
              <span class="text-sm font-medium text-blue-600">{{
                index + 1
              }}</span>
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-900">
                {{ getLocationName(locationId) }}
              </p>
              <p class="text-xs text-gray-500">
                {{ getLocationAddress(locationId) }}
              </p>
            </div>
            <div class="text-sm text-gray-500">
              {{ getLocationTimeWindow(locationId) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="px-6 py-4 bg-gray-50 flex justify-end space-x-3">
        <button
          @click="$emit('save')"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          Сохранить маршрут
        </button>
        <button
          @click="$emit('reset')"
          class="px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          Новая оптимизация
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Route } from '@/services/types'

const props = defineProps<{
  result: Route | null
  isLoading: boolean
  error: string | null
  originalMetrics?: {
    total_distance_km: number
    total_time_hours: number
    total_cost_rub: number
  } | null
  locations: Array<{
    id: string
    name: string
    address: string
    time_window_start: string
    time_window_end: string
  }>
}>()

defineEmits<{
  reset: []
  retry: []
  save: []
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

const getLocationName = (locationId: string): string => {
  if (!props.locations || !props.locations.length) return locationId
  const location = props.locations.find((l) => l.id === locationId)
  return location?.name || locationId
}

const getLocationAddress = (locationId: string): string => {
  if (!props.locations || !props.locations.length) return ''
  const location = props.locations.find((l) => l.id === locationId)
  return location?.address || ''
}

const getLocationTimeWindow = (locationId: string): string => {
  if (!props.locations || !props.locations.length) return ''
  const location = props.locations.find((l) => l.id === locationId)
  if (!location) return ''
  return `${location.time_window_start} - ${location.time_window_end}`
}

// Числовое значение для сравнения
const improvementPercentageNumber = computed(() => {
  if (!props.originalMetrics || !props.result) return 0

  const originalTotal =
    props.originalMetrics.total_distance_km * 0.3 +
    props.originalMetrics.total_time_hours * 0.3 +
    props.originalMetrics.total_cost_rub * 0.4

  const optimizedTotal =
    props.result.total_distance_km * 0.3 +
    props.result.total_time_hours * 0.3 +
    props.result.total_cost_rub * 0.4

  const improvement = ((originalTotal - optimizedTotal) / originalTotal) * 100
  return Math.max(0, improvement)
})

// Строковое значение для отображения
const improvementPercentageString = computed(() => {
  return improvementPercentageNumber.value.toFixed(1)
})
</script>
