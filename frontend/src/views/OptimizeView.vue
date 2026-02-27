<template>
  <div class="py-6 md:py-8">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-2xl md:text-3xl font-bold text-gray-900">
        Оптимизация маршрута
      </h1>
      <p class="mt-2 text-gray-600">
        Настройте параметры, выберите модель и запустите оптимизацию — получите 3 варианта на выбор
      </p>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════════
         СОСТОЯНИЕ 1: Форма ввода + боковая панель
    ════════════════════════════════════════════════════════════════════════ -->
    <template v-if="currentView === 'form'">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
        <!-- Форма -->
        <div class="lg:col-span-2 space-y-6">
          <OptimizationForm
            ref="optimizationForm"
            @submit="handleSubmit"
            @validate="handleValidation"
          />
        </div>

        <!-- Боковая панель -->
        <div class="space-y-6">
          <!-- Выбор модели -->
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
                      <span :class="model.textColor" class="font-bold text-sm">{{
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

          <!-- Загрузка файла -->
          <FileUpload @add-locations="handleAddLocationsFromFile" />

          <!-- Ограничения -->
          <ConstraintsPanel
            :constraints="constraints"
            @update-constraints="handleConstraintsUpdate"
          />
        </div>
      </div>

      <!-- Кнопки формы -->
      <div class="mt-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="text-sm text-gray-600">
          <p>Все поля обязательны для заполнения</p>
          <p class="mt-1">Минимум 2 магазина для оптимизации маршрута</p>
        </div>
        <div class="flex space-x-3">
          <button
            type="button"
            @click="resetForm"
            class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Сбросить
          </button>
          <button
            type="button"
            @click="handleOptimize"
            :disabled="!isFormValid"
            class="px-6 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Оптимизировать маршрут
          </button>
        </div>
      </div>
    </template>

    <!-- ═══════════════════════════════════════════════════════════════════════
         СОСТОЯНИЕ 2: Прогресс-бар ожидания LLM
    ════════════════════════════════════════════════════════════════════════ -->
    <template v-else-if="currentView === 'loading'">
      <div class="max-w-2xl mx-auto">
        <OptimizationProgress
          :model="selectedModel"
          :done="loadingDone"
        />
      </div>
    </template>

    <!-- ═══════════════════════════════════════════════════════════════════════
         СОСТОЯНИЕ 2б: Ошибка при загрузке
    ════════════════════════════════════════════════════════════════════════ -->
    <template v-else-if="currentView === 'error'">
      <div class="max-w-2xl mx-auto">
        <div class="bg-white rounded-xl shadow-sm border border-red-200 p-8 text-center">
          <div class="inline-flex items-center justify-center w-14 h-14 bg-red-100 rounded-full mb-4">
            <svg class="w-7 h-7 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">Ошибка оптимизации</h3>
          <p class="text-gray-600 mb-6">{{ optimizationError }}</p>
          <div class="flex justify-center gap-3">
            <button
              @click="currentView = 'form'"
              class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Изменить параметры
            </button>
            <button
              @click="handleOptimize"
              class="px-6 py-2 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              Повторить
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- ═══════════════════════════════════════════════════════════════════════
         СОСТОЯНИЕ 3: Выбор из 3 вариантов
    ════════════════════════════════════════════════════════════════════════ -->
    <template v-else-if="currentView === 'variants' && variantsResponse">
      <div class="max-w-2xl mx-auto">
        <OptimizationVariants
          :variants="variantsResponse.variants"
          :model-used="variantsResponse.model_used"
          :llm-evaluation-success="variantsResponse.llm_evaluation_success"
          :response-time-ms="variantsResponse.response_time_ms"
          @select="handleVariantSelect"
          @reset="resetAll"
        />
      </div>
    </template>

    <!-- ═══════════════════════════════════════════════════════════════════════
         СОСТОЯНИЕ 4: Результат выбранного варианта
    ════════════════════════════════════════════════════════════════════════ -->
    <template v-else-if="currentView === 'result'">
      <div class="max-w-3xl mx-auto">
        <OptimizationResult
          :result="optimizationResult"
          :is-loading="false"
          :error="null"
          :original-metrics="originalMetrics"
          :locations="formLocations"
          @reset="resetAll"
          @retry="handleOptimize"
          @save="saveRoute"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import OptimizationForm from '@/components/optimize/OptimizationForm.vue'
import OptimizationResult from '@/components/optimize/OptimizationResult.vue'
import OptimizationProgress from '@/components/optimize/OptimizationProgress.vue'
import OptimizationVariants from '@/components/optimize/OptimizationVariants.vue'
import ConstraintsPanel from '@/components/optimize/ConstraintsPanel.vue'
import FileUpload from '@/components/optimize/FileUpload.vue'
import { optimizeVariants, confirmVariant } from '@/services/api'
import type { Constraints, Location } from '@/components/optimize/types'
import type { Route, RouteVariant, OptimizeVariantsResponse } from '@/services/types'

// ─── Модели ────────────────────────────────────────────────────────────────────
const models = [
  {
    id: 'qwen',
    name: 'Qwen 0.5B',
    label: 'Q',
    description: 'Быстрее, меньше памяти',
    color: 'bg-purple-100',
    textColor: 'text-purple-600'
  },
  {
    id: 'llama',
    name: 'Llama 1B',
    label: 'L',
    description: 'Точнее, больше контекст',
    color: 'bg-green-100',
    textColor: 'text-green-600'
  },
]

// ─── Машина состояний ──────────────────────────────────────────────────────────
type ViewState = 'form' | 'loading' | 'error' | 'variants' | 'result'
const currentView = ref<ViewState>('form')

// ─── Состояние формы ──────────────────────────────────────────────────────────
const selectedModel = ref<string>('qwen')
const constraints = ref<Constraints>({
  vehicleCapacity: 1,
  maxDistance: 500,
  startTime: '08:00',
  endTime: '20:00'
})
const isFormValid = ref(false)
const optimizationForm = ref<InstanceType<typeof OptimizationForm> | null>(null)

// ─── Данные ────────────────────────────────────────────────────────────────────
const loadingDone = ref(false)
const variantsResponse = ref<OptimizeVariantsResponse | null>(null)
const selectedVariant = ref<RouteVariant | null>(null)
const optimizationResult = ref<Route | null>(null)
const optimizationError = ref<string | null>(null)
const locationIds = ref<string[]>([])

const originalMetrics = ref<{
  total_distance_km: number
  total_time_hours: number
  total_cost_rub: number
} | null>(null)

const formLocations = ref<Array<{
  id: string
  name: string
  address: string
  time_window_start: string
  time_window_end: string
}>>([])

// ─── Обработчики формы ────────────────────────────────────────────────────────
const handleSubmit = (formData: any) => {
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
    optimizationForm.value.clearAllLocations()
    await nextTick()
    locations.forEach((location) => {
      optimizationForm.value?.addLocationFromImport(location)
    })
    console.log(`Добавлено ${locations.length} магазинов из файла`)
  }
}

// ─── Основной сценарий оптимизации ────────────────────────────────────────────
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

  // Собираем данные формы
  formLocations.value = (formData.locations ?? []).map((loc: any) => ({
    id: loc.id,
    name: loc.name,
    address: `г. ${loc.city ?? ''}, ул. ${loc.street ?? ''}, д. ${loc.houseNumber ?? ''}`,
    time_window_start: loc.timeWindowStart ?? '',
    time_window_end: loc.timeWindowEnd ?? ''
  }))

  locationIds.value = (formData.locations ?? []).map((loc: any) => loc.id)

  // Исходные метрики (приблизительные)
  originalMetrics.value = {
    total_distance_km: locationIds.value.length * 15,
    total_time_hours: locationIds.value.length * 1.5,
    total_cost_rub: locationIds.value.length * 1000
  }

  // Переходим в состояние загрузки
  loadingDone.value = false
  variantsResponse.value = null
  optimizationError.value = null
  currentView.value = 'loading'

  try {
    const result = await optimizeVariants(
      locationIds.value,
      selectedModel.value,
      {
        vehicle_capacity: constraints.value.vehicleCapacity,
        max_distance_km: constraints.value.maxDistance,
        start_time: constraints.value.startTime,
        end_time: constraints.value.endTime,
      }
    )

    // Сигнализируем прогресс-бару что готово
    loadingDone.value = true

    // Небольшая пауза для анимации прогресс-бара до 100%
    await new Promise(resolve => setTimeout(resolve, 600))

    variantsResponse.value = result
    currentView.value = 'variants'

  } catch (error: any) {
    loadingDone.value = true
    console.error('Variants generation error:', error)
    optimizationError.value =
      error?.detail ||
      error?.message ||
      'Не удалось выполнить оптимизацию. Проверьте подключение к серверу.'
    await new Promise(resolve => setTimeout(resolve, 300))
    currentView.value = 'error'
  }
}

// ─── Выбор варианта ───────────────────────────────────────────────────────────
const handleVariantSelect = (variant: RouteVariant) => {
  selectedVariant.value = variant

  // Конвертируем RouteVariant в Route для отображения в OptimizationResult
  optimizationResult.value = {
    id: `variant-${variant.id}-${Date.now()}`,
    name: variant.name,
    locations: variant.locations,
    total_distance_km: variant.metrics.distance_km,
    total_time_hours: variant.metrics.time_hours,
    total_cost_rub: variant.metrics.cost_rub,
    model_used: variantsResponse.value?.model_used ?? selectedModel.value,
    fallback_reason: null,
    created_at: new Date().toISOString(),
  }

  currentView.value = 'result'
}

// ─── Сохранение выбранного варианта ──────────────────────────────────────────
const saveRoute = async () => {
  if (!selectedVariant.value || !variantsResponse.value) {
    alert('Нет данных для сохранения')
    return
  }

  try {
    await confirmVariant({
      name: selectedVariant.value.name,
      locations: selectedVariant.value.locations,
      total_distance_km: selectedVariant.value.metrics.distance_km,
      total_time_hours: selectedVariant.value.metrics.time_hours,
      total_cost_rub: selectedVariant.value.metrics.cost_rub,
      quality_score: selectedVariant.value.metrics.quality_score,
      model_used: variantsResponse.value.model_used,
      original_location_ids: locationIds.value,
    })
    alert('Маршрут успешно сохранён!')
  } catch (err: any) {
    console.error('Save error:', err)
    alert('Ошибка при сохранении маршрута')
  }
}

// ─── Сброс ────────────────────────────────────────────────────────────────────
const resetAll = () => {
  currentView.value = 'form'
  variantsResponse.value = null
  selectedVariant.value = null
  optimizationResult.value = null
  optimizationError.value = null
  originalMetrics.value = null
  formLocations.value = []
  locationIds.value = []
  loadingDone.value = false
  resetForm()
}

const resetForm = () => {
  if (optimizationForm.value) {
    optimizationForm.value.resetForm()
  }
  selectedModel.value = 'qwen'
  constraints.value = {
    vehicleCapacity: 1,
    maxDistance: 500,
    startTime: '08:00',
    endTime: '20:00'
  }
}
</script>
