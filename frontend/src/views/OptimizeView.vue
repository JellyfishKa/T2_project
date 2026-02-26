<template>
  <div class="py-6 md:py-8">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-2xl md:text-3xl font-bold text-gray-900">
        Оптимизация маршрута
      </h1>
      <p class="mt-2 text-gray-600">
        Настройте параметры и запустите оптимизацию маршрута с использованием
        выбранной LLM модели
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
      <!-- Main Form -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Форма оптимизации (скрываем после успешной оптимизации) -->
        <OptimizationForm
          v-if="!optimizationResult"
          ref="optimizationForm"
          @submit="handleSubmit"
          @validate="handleValidation"
        />

        <!-- Результат оптимизации -->
        <OptimizationResult
          v-else
          :result="optimizationResult"
          :is-loading="isOptimizing"
          :error="optimizationError"
          :original-metrics="originalMetrics"
          :locations="formLocations"
          @reset="resetOptimization"
          @retry="retryOptimization"
          @save="saveRoute"
        />
      </div>

      <!-- Side Panel (скрываем после успешной оптимизации) -->
      <div v-if="!optimizationResult" class="space-y-6">
        <!-- Model Selection -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Выбор модели</h3>

          <div class="space-y-3">
            <label
              v-for="model in models"
              :key="model.id"
              class="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              :class="
                selectedModel === model.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200'
              "
            >
              <input
                type="radio"
                v-model="selectedModel"
                :value="model.id"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              />
              <div class="ml-3">
                <div class="flex items-center">
                  <div
                    :class="model.color"
                    class="h-8 w-8 rounded-lg flex items-center justify-center mr-2"
                  >
                    <span :class="model.textColor" class="font-bold">{{
                      model.label
                    }}</span>
                  </div>
                  <div>
                    <div class="text-sm font-medium text-gray-900">
                      {{ model.name }}
                    </div>
                    <div class="text-xs text-gray-500">
                      {{ model.description }}
                    </div>
                  </div>
                </div>
              </div>
            </label>
          </div>
        </div>

        <!-- File Upload -->
        <FileUpload @add-locations="handleAddLocationsFromFile" />

        <!-- Constraints Summary -->
        <ConstraintsPanel
          :constraints="constraints"
          @update-constraints="handleConstraintsUpdate"
        />
      </div>
    </div>

    <!-- Form Actions (скрываем после успешной оптимизации) -->
    <div
      v-if="!optimizationResult"
      class="mt-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
    >
      <div class="text-sm text-gray-600">
        <p>Все поля обязательны для заполнения</p>
        <p class="mt-1">Минимум 2 магазина для оптимизации маршрута</p>
      </div>
      <div class="flex space-x-3">
        <button
          type="button"
          @click="resetForm"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          :disabled="isOptimizing"
        >
          Сбросить
        </button>
        <button
          type="button"
          @click="handleOptimize"
          :disabled="!isFormValid || isOptimizing"
          class="px-6 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="isOptimizing" class="flex items-center">
            <svg
              class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            Оптимизация...
          </span>
          <span v-else>Оптимизировать маршрут</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import OptimizationForm from '@/components/optimize/OptimizationForm.vue'
import OptimizationResult from '@/components/optimize/OptimizationResult.vue'
import ConstraintsPanel from '@/components/optimize/ConstraintsPanel.vue'
import FileUpload from '@/components/optimize/FileUpload.vue'
import { optimize } from '@/services/api'
import type { Constraints, Location } from '@/components/optimize/types'
import type { Route } from '@/services/types'

// Models
const models = [
  {
    id: 'llama',
    name: 'Llama',
    label: 'L',
    description: 'Высокая точность, платный',
    color: 'bg-green-100',
    textColor: 'text-green-600'
  },
  {
    id: 'qwen',
    name: 'Qwen',
    label: 'Q',
    description: 'Быстрый, бесплатный',
    color: 'bg-purple-100',
    textColor: 'text-purple-600'
  },
]

// State
const selectedModel = ref('llama')
const constraints = ref<Constraints>({
  vehicleCapacity: 1,
  maxDistance: 500,
  startTime: '08:00',
  endTime: '20:00'
})
const isFormValid = ref(false)
const isOptimizing = ref(false)
const optimizationResult = ref<Route | null>(null)
const optimizationError = ref<string | null>(null)
const originalMetrics = ref<{
  total_distance_km: number
  total_time_hours: number
  total_cost_rub: number
} | null>(null)
const formLocations = ref<
  Array<{
    id: string
    name: string
    address: string
    time_window_start: string
    time_window_end: string
  }>
>([])

const optimizationForm = ref<InstanceType<typeof OptimizationForm> | null>(null)

// Methods
const handleSubmit = (formData: any) => {
  // Сохраняем локации для отображения в результатах
  formLocations.value = formData.locations.map((loc: any) => ({
    id: loc.id,
    name: loc.name,
    address: `г. ${loc.city}, ул. ${loc.street}, д. ${loc.houseNumber}`,
    time_window_start: loc.timeWindowStart,
    time_window_end: loc.timeWindowEnd
  }))
}

const handleValidation = (isValid: boolean) => {
  isFormValid.value = isValid
}

const handleConstraintsUpdate = (updatedConstraints: Constraints) => {
  constraints.value = updatedConstraints
}

const handleAddLocationsFromFile = async (locations: Location[]) => {
  if (optimizationForm.value && locations.length > 0) {
    // Очищаем текущие локации и добавляем новые из файла
    optimizationForm.value.clearAllLocations()
    await nextTick()

    // Добавляем каждую локацию из файла
    locations.forEach((location) => {
      optimizationForm.value?.addLocationFromImport(location)
    })

    // Показываем сообщение об успехе (можно добавить уведомление)
    console.log(`Добавлено ${locations.length} магазинов из файла`)
  }
}

const handleOptimize = async () => {
  if (!isFormValid.value) {
    alert('Пожалуйста, заполните все обязательные поля формы')
    return
  }

  if (!optimizationForm.value) {
    alert('Ошибка формы')
    return
  }

  const formData = optimizationForm.value.getFormData()

  // Сохраняем локации для отображения имён в результатах
  formLocations.value = (formData.locations ?? []).map((loc: any) => ({
    id: loc.id,
    name: loc.name,
    address: `г. ${loc.city ?? ''}, ул. ${loc.street ?? ''}, д. ${loc.houseNumber ?? ''}`,
    time_window_start: loc.timeWindowStart ?? '',
    time_window_end: loc.timeWindowEnd ?? ''
  }))

  // Сохраняем исходные метрики для расчета улучшения
  const locationIds = (formData.locations ?? []).map((loc: any) => loc.id)

  // Рассчитываем примерные исходные метрики (можно заменить на реальные от бэкенда)
  originalMetrics.value = {
    total_distance_km: locationIds.length * 15, // Пример: 15 км на магазин
    total_time_hours: locationIds.length * 1.5, // Пример: 1.5 часа на магазин
    total_cost_rub: locationIds.length * 1000 // Пример: 1000₽ на магазин
  }

  try {
    isOptimizing.value = true
    optimizationError.value = null

    const result = await optimize(locationIds, selectedModel.value, {
      vehicle_capacity: constraints.value.vehicleCapacity,
      max_distance_km: constraints.value.maxDistance,
      start_time: constraints.value.startTime,
      end_time: constraints.value.endTime,
      max_stops: constraints.value.maxStops
    })

    optimizationResult.value = result
  } catch (error: any) {
    console.error('Optimization error:', error)
    optimizationError.value =
      error.message || 'Не удалось выполнить оптимизацию'
  } finally {
    isOptimizing.value = false
  }
}

const retryOptimization = () => {
  optimizationError.value = null
  handleOptimize()
}

const resetOptimization = () => {
  optimizationResult.value = null
  optimizationError.value = null
  originalMetrics.value = null
  formLocations.value = []
  resetForm()
}

const resetForm = () => {
  if (optimizationForm.value) {
    optimizationForm.value.resetForm()
  }
  selectedModel.value = 'llama'
  constraints.value = {
    vehicleCapacity: 1,
    maxDistance: 500,
    startTime: '08:00',
    endTime: '20:00'
  }
}

const saveRoute = async () => {
  if (!optimizationResult.value) return

  // Здесь можно добавить логику сохранения маршрута
  alert('Маршрут сохранен!')
}
</script>
