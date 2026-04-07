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
      <div class="max-w-3xl mx-auto">
        <OptimizationVariants
          :variants="variantsResponse.variants"
          :locations="formLocations"
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
          :original-location-ids="originalLocationIds"
          :route-source="resultRouteSource"
          :route-label="resultRouteLabel"
          :is-updating-metrics="isUpdatingResultMetrics"
          :can-restore-original="canRestoreOriginal"
          :can-restore-ai="canRestoreAi"
          :ai-route-label="selectedAiVariantName"
          :original-route-source="originalRouteSource"
          :original-traffic-lights-count="originalTrafficLightsCount"
          :current-route-source="currentRouteSource"
          :current-traffic-lights-count="currentTrafficLightsCount"
          :llm-evaluation-status="resultLlmEvaluationStatus"
          :llm-quality-score="resultLlmQualityScore"
          @reset="resetAll"
          @retry="handleOptimize"
          @save="saveRoute"
          @move-location="handleMoveResultLocation"
          @reorder-locations="handleReorderResultLocations"
          @restore-original="restoreOriginalRoute"
          @restore-ai="restoreAiRoute"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch } from 'vue'
import OptimizationForm from '@/components/optimize/OptimizationForm.vue'
import OptimizationResult from '@/components/optimize/OptimizationResult.vue'
import OptimizationProgress from '@/components/optimize/OptimizationProgress.vue'
import OptimizationVariants from '@/components/optimize/OptimizationVariants.vue'
import ConstraintsPanel from '@/components/optimize/ConstraintsPanel.vue'
import FileUpload from '@/components/optimize/FileUpload.vue'
import { buildLocationAddress } from '@/components/optimize/address'
import { optimizeVariants, confirmVariant, fetchRoutePreview } from '@/services/api'
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
type ResultRouteSource = 'original' | 'ai' | 'manual'
type RoutePreviewSource = 'road_network' | 'fallback' | 'client_fallback' | 'empty' | 'single_point'
type LlmEvaluationStatus = 'current' | 'stale' | 'unavailable'

interface RouteMetricsDetails {
  total_distance_km: number
  total_time_hours: number
  total_cost_rub: number
  source: RoutePreviewSource
  traffic_lights_count: number
}

const currentView = ref<ViewState>('form')

// ─── Состояние формы ──────────────────────────────────────────────────────────
const savedModel = localStorage.getItem('t2_preferred_model') ?? 'qwen'
const selectedModel = ref<string>(savedModel)
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
const routeName = ref('')
const originalLocationIds = ref<string[]>([])
const resultRouteSource = ref<ResultRouteSource>('original')
const resultRouteLabel = ref<string | null>(null)
const selectedAiVariantName = ref<string | null>(null)
const selectedAiVariantLocationIds = ref<string[] | null>(null)
const selectedAiVariantQualityScore = ref<number>(0)
const isUpdatingResultMetrics = ref(false)
const originalRouteSource = ref<RoutePreviewSource>('empty')
const originalTrafficLightsCount = ref(0)
const currentRouteSource = ref<RoutePreviewSource>('empty')
const currentTrafficLightsCount = ref(0)

const originalMetrics = ref<{
  total_distance_km: number
  total_time_hours: number
  total_cost_rub: number
} | null>(null)

const formLocations = ref<Array<{
  id: string
  name: string
  address: string
  lat: number
  lon: number
  time_window_start: string
  time_window_end: string
}>>([])

const canRestoreOriginal = computed(() =>
  !!optimizationResult.value &&
  originalLocationIds.value.length > 0 &&
  optimizationResult.value.locations.join('|') !== originalLocationIds.value.join('|')
)

const canRestoreAi = computed(() =>
  !!optimizationResult.value &&
  !!selectedAiVariantLocationIds.value?.length &&
  optimizationResult.value.locations.join('|') !== selectedAiVariantLocationIds.value.join('|')
)

const resultLlmEvaluationStatus = computed<LlmEvaluationStatus>(() => {
  if (!optimizationResult.value) return 'unavailable'
  if (
    selectedAiVariantLocationIds.value?.length &&
    optimizationResult.value.locations.join('|') === selectedAiVariantLocationIds.value.join('|') &&
    selectedAiVariantQualityScore.value > 0
  ) {
    return 'current'
  }
  if (resultRouteSource.value === 'manual') {
    return 'stale'
  }
  return 'unavailable'
})

const resultLlmQualityScore = computed<number | null>(() =>
  resultLlmEvaluationStatus.value === 'current' ? selectedAiVariantQualityScore.value : null
)

// Сохранять выбранную модель в localStorage
watch(selectedModel, (v) => localStorage.setItem('t2_preferred_model', v))

// ─── Обработчики формы ────────────────────────────────────────────────────────
const handleSubmit = (formData: any) => {
  routeName.value = formData.routeName ?? ''
  formLocations.value = formData.locations.map((loc: any) => ({
    id: loc.id,
    name: loc.name,
    address: buildLocationAddress(loc),
    lat: Number(loc.latitude),
    lon: Number(loc.longitude),
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
  routeName.value = formData.routeName ?? ''

  // Собираем данные формы
  formLocations.value = (formData.locations ?? []).map((loc: any) => ({
    id: loc.id,
    name: loc.name,
    address: buildLocationAddress(loc),
    lat: Number(loc.latitude),
    lon: Number(loc.longitude),
    time_window_start: loc.timeWindowStart ?? '',
    time_window_end: loc.timeWindowEnd ?? ''
  }))

  locationIds.value = (formData.locations ?? []).map((loc: any) => loc.id)
  originalLocationIds.value = [...locationIds.value]
  selectedAiVariantName.value = null
  selectedAiVariantLocationIds.value = null
  selectedAiVariantQualityScore.value = 0
  resultRouteSource.value = 'original'
  resultRouteLabel.value = null

  // Исходные метрики маршрута в текущем порядке точек.
  const initialMetrics = await getRouteMetrics(locationIds.value)
  originalMetrics.value = initialMetrics
  originalRouteSource.value = initialMetrics.source
  originalTrafficLightsCount.value = initialMetrics.traffic_lights_count

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
  selectedAiVariantName.value = variant.name
  selectedAiVariantLocationIds.value = [...variant.locations]
  selectedAiVariantQualityScore.value = variant.metrics.quality_score
  resultRouteSource.value = 'ai'
  resultRouteLabel.value = variant.name

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
  currentRouteSource.value = 'road_network'
  currentTrafficLightsCount.value = 0

  currentView.value = 'result'
  void applyResultRoute(variant.locations, 'ai', variant.name)
}

// ─── Сохранение выбранного варианта ──────────────────────────────────────────
const saveRoute = async () => {
  if (!optimizationResult.value || !variantsResponse.value) {
    alert('Нет данных для сохранения')
    return
  }

  try {
    const qualityScore =
      selectedAiVariantLocationIds.value?.join('|') === optimizationResult.value.locations.join('|')
        ? selectedAiVariantQualityScore.value
        : 0

    await confirmVariant({
      name: optimizationResult.value.name,
      locations: optimizationResult.value.locations,
      total_distance_km: optimizationResult.value.total_distance_km,
      total_time_hours: optimizationResult.value.total_time_hours,
      total_cost_rub: optimizationResult.value.total_cost_rub,
      quality_score: qualityScore,
      model_used: variantsResponse.value.model_used,
      original_location_ids: originalLocationIds.value,
    })
    alert(
      qualityScore > 0
        ? 'Маршрут успешно сохранён!'
        : 'Маршрут успешно сохранён без LLM-оценки для текущего порядка.'
    )
  } catch (err: any) {
    console.error('Save error:', err)
    alert('Ошибка при сохранении маршрута')
  }
}

async function getRouteMetrics(routeLocationIds: string[]): Promise<RouteMetricsDetails> {
  const points = routeLocationIds
    .map((locationId) => formLocations.value.find((location) => location.id === locationId))
    .filter((location): location is NonNullable<typeof formLocations.value[number]> => !!location)

  if (points.length < 2) {
    return {
      total_distance_km: 0,
      total_time_hours: 0,
      total_cost_rub: 0,
      source: points.length === 1 ? 'single_point' : 'empty',
      traffic_lights_count: 0,
    }
  }

  try {
    const preview = await fetchRoutePreview(
      points.map((location) => ({
        lat: location.lat,
        lon: location.lon,
      }))
    )

    return {
      total_distance_km: preview.distance_km,
      total_time_hours: preview.time_minutes / 60,
      total_cost_rub: preview.cost_rub,
      source: (preview.source as RoutePreviewSource) ?? 'road_network',
      traffic_lights_count: preview.traffic_lights_count ?? 0,
    }
  } catch {
    const fallbackStops = Math.max(routeLocationIds.length, points.length)
    return {
      total_distance_km: fallbackStops * 15,
      total_time_hours: fallbackStops * 1.5,
      total_cost_rub: fallbackStops * 1000,
      source: 'client_fallback',
      traffic_lights_count: 0,
    }
  }
}

function buildRouteName(source: ResultRouteSource, label?: string | null) {
  if (source === 'ai') {
    return label || routeName.value || 'Маршрут от ИИ'
  }
  if (source === 'manual') {
    return routeName.value
      ? `${routeName.value} (ручная перестановка)`
      : 'Маршрут (ручная перестановка)'
  }
  return routeName.value
    ? `${routeName.value} (исходный порядок)`
    : 'Маршрут (исходный порядок)'
}

async function applyResultRoute(
  routeLocationIds: string[],
  source: ResultRouteSource,
  label?: string | null,
) {
  if (!optimizationResult.value && currentView.value !== 'result') {
    return
  }

  isUpdatingResultMetrics.value = true
  try {
    const metrics = await getRouteMetrics(routeLocationIds)
    optimizationResult.value = {
      id: optimizationResult.value?.id ?? `route-${Date.now()}`,
      name: buildRouteName(source, label),
      locations: [...routeLocationIds],
      total_distance_km: metrics.total_distance_km,
      total_time_hours: metrics.total_time_hours,
      total_cost_rub: metrics.total_cost_rub,
      model_used: variantsResponse.value?.model_used ?? selectedModel.value,
      fallback_reason: null,
      created_at: optimizationResult.value?.created_at ?? new Date().toISOString(),
    }
    currentRouteSource.value = metrics.source
    currentTrafficLightsCount.value = metrics.traffic_lights_count
    resultRouteSource.value = source
    resultRouteLabel.value = label ?? null
  } finally {
    isUpdatingResultMetrics.value = false
  }
}

function handleMoveResultLocation(payload: { index: number; direction: -1 | 1 }) {
  if (!optimizationResult.value) return

  const nextIndex = payload.index + payload.direction
  if (nextIndex < 0 || nextIndex >= optimizationResult.value.locations.length) return

  const nextOrder = [...optimizationResult.value.locations]
  ;[nextOrder[payload.index], nextOrder[nextIndex]] = [nextOrder[nextIndex], nextOrder[payload.index]]
  void applyResultRoute(nextOrder, 'manual', 'Ручной порядок')
}

function handleReorderResultLocations(payload: { fromIndex: number; toIndex: number }) {
  if (!optimizationResult.value) return
  if (payload.fromIndex === payload.toIndex) return
  if (payload.fromIndex < 0 || payload.toIndex < 0) return
  if (payload.fromIndex >= optimizationResult.value.locations.length) return
  if (payload.toIndex >= optimizationResult.value.locations.length) return

  const nextOrder = [...optimizationResult.value.locations]
  const [movedLocation] = nextOrder.splice(payload.fromIndex, 1)
  nextOrder.splice(payload.toIndex, 0, movedLocation)
  void applyResultRoute(nextOrder, 'manual', 'Ручной порядок')
}

function restoreOriginalRoute() {
  if (!originalLocationIds.value.length) return
  void applyResultRoute(originalLocationIds.value, 'original')
}

function restoreAiRoute() {
  if (!selectedAiVariantLocationIds.value?.length) return
  void applyResultRoute(selectedAiVariantLocationIds.value, 'ai', selectedAiVariantName.value)
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
  originalLocationIds.value = []
  routeName.value = ''
  resultRouteSource.value = 'original'
  resultRouteLabel.value = null
  selectedAiVariantName.value = null
  selectedAiVariantLocationIds.value = null
  selectedAiVariantQualityScore.value = 0
  isUpdatingResultMetrics.value = false
  originalRouteSource.value = 'empty'
  originalTrafficLightsCount.value = 0
  currentRouteSource.value = 'empty'
  currentTrafficLightsCount.value = 0
  loadingDone.value = false
  resetForm()
}

const resetForm = () => {
  if (optimizationForm.value) {
    optimizationForm.value.resetForm()
  }
  selectedModel.value = localStorage.getItem('t2_preferred_model') ?? 'qwen'
  constraints.value = {
    vehicleCapacity: 1,
    maxDistance: 500,
    startTime: '08:00',
    endTime: '20:00'
  }
}
</script>
