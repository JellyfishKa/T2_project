<template>
  <div
    class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
  >
    <!-- Header with model info - показываем только если есть result -->
    <div
      v-if="result"
      class="px-6 py-5 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50"
    >
      <div class="flex items-center justify-between gap-4">
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
          <div class="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span
              class="inline-flex items-center px-2.5 py-1 rounded-full font-medium"
              :class="routeSourceBadgeClass"
            >
              {{ routeSourceLabel }}
            </span>
            <span v-if="routeLabel" class="text-gray-500">
              {{ routeLabel }}
            </span>
            <span
              class="inline-flex items-center px-2.5 py-1 rounded-full font-medium"
              :class="llmStatusBadgeClass"
            >
              {{ llmStatusLabel }}
            </span>
            <span v-if="isUpdatingMetrics" class="text-blue-600">
              Пересчитываю маршрут…
            </span>
          </div>
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

      <div
        v-if="originalRouteWarning || currentRouteWarning || llmEvaluationStatus !== 'current'"
        class="px-6 py-4 bg-amber-50 border-y border-amber-200"
      >
        <div class="space-y-2 text-sm text-amber-900">
          <p v-if="currentRouteWarning">
            Текущий маршрут: {{ currentRouteWarning }}
          </p>
          <p v-if="originalRouteWarning">
            Исходный маршрут: {{ originalRouteWarning }}
          </p>
          <p v-if="llmEvaluationStatus === 'stale'">
            LLM-оценка снята: после ручной перестановки этот порядок не сравнивался моделью.
          </p>
          <p v-else-if="llmEvaluationStatus === 'unavailable'">
            Для текущего порядка нет актуальной LLM-оценки.
          </p>
        </div>
      </div>

      <div
        v-if="originalLocationIds.length >= 2"
        class="px-6 py-5 bg-blue-50/40 border-y border-blue-100"
      >
        <div class="flex items-center justify-between gap-3 mb-4">
          <div>
            <h4 class="text-sm font-medium text-gray-900">Сравнение маршрутов</h4>
            <p class="text-xs text-gray-500">
              Слева исходный порядок точек, справа текущая версия маршрута.
            </p>
          </div>
          <span class="text-xs text-gray-500">
            {{ isUpdatingMetrics ? 'Данные обновляются…' : 'Сравнение по карте и метрикам' }}
          </span>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div class="bg-white border border-gray-200 rounded-lg p-4">
            <p class="text-xs font-semibold text-gray-700 mb-1">До изменений</p>
            <p class="text-xs text-gray-500 mb-3">{{ originalMetricsLabel }}</p>
            <p v-if="originalRouteHint" class="text-xs text-amber-700 mb-3">
              {{ originalRouteHint }}
            </p>
            <div class="space-y-2 max-h-48 overflow-y-auto mb-4">
              <div
                v-for="(locationId, index) in originalLocationIds"
                :key="`${locationId}-original-${index}`"
                class="flex items-center gap-2 text-xs"
              >
                <span class="text-gray-400 w-4">{{ index + 1 }}</span>
                <div class="min-w-0">
                  <p class="font-medium text-gray-800 truncate">{{ getLocationName(locationId) }}</p>
                  <p class="text-gray-500 truncate">{{ getLocationAddress(locationId) }}</p>
                </div>
              </div>
            </div>
            <RouteMap v-if="originalMapPoints.length >= 2" :points="originalMapPoints" height="14rem" />
          </div>

          <div class="bg-white border border-gray-200 rounded-lg p-4">
            <p class="text-xs font-semibold text-gray-700 mb-1">После изменений</p>
            <p class="text-xs text-gray-500 mb-3">{{ currentMetricsLabel }}</p>
            <p v-if="currentRouteHint" class="text-xs text-amber-700 mb-3">
              {{ currentRouteHint }}
            </p>
            <div class="space-y-2 max-h-48 overflow-y-auto mb-4">
              <div
                v-for="(locationId, index) in result.locations"
                :key="`${locationId}-current-${index}`"
                class="flex items-center gap-2 text-xs"
              >
                <span class="text-gray-400 w-4">{{ index + 1 }}</span>
                <div class="min-w-0">
                  <p class="font-medium text-gray-800 truncate">{{ getLocationName(locationId) }}</p>
                  <p class="text-gray-500 truncate">{{ getLocationAddress(locationId) }}</p>
                </div>
              </div>
            </div>
            <RouteMap v-if="mapPoints.length >= 2" :points="mapPoints" height="14rem" />
          </div>
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
        <div class="flex items-center justify-between gap-3 mb-4">
          <div>
            <h4 class="text-sm font-medium text-gray-900">
              Текущий порядок посещения
            </h4>
            <p class="text-xs text-gray-500 mt-1">
              Перетаскивайте точки мышью или меняйте очередность кнопками, карта и метрики обновятся сразу.
            </p>
          </div>
          <div class="flex flex-wrap justify-end gap-2">
            <button
              v-if="canRestoreAi"
              type="button"
              class="px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
              @click="$emit('restore-ai')"
            >
              Вернуть {{ aiRouteLabel || 'вариант ИИ' }}
            </button>
            <button
              v-if="canRestoreOriginal"
              type="button"
              class="px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
              @click="$emit('restore-original')"
            >
              Откатить к исходному
            </button>
          </div>
        </div>
        <div class="space-y-3 max-h-96 overflow-y-auto pr-1">
          <div
            v-for="(locationId, index) in result.locations"
            :key="`${locationId}-${index}`"
            class="flex items-center gap-3 rounded-lg border px-3 py-2 transition-colors"
            :class="dragOverIndex === index ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-white'"
            :draggable="!isUpdatingMetrics"
            @dragstart="onDragStart(index, $event)"
            @dragenter.prevent="onDragEnter(index)"
            @dragover.prevent="onDragEnter(index)"
            @drop.prevent="onDrop(index)"
            @dragend="onDragEnd"
          >
            <div
              class="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3"
            >
              <span class="text-sm font-medium text-blue-600">{{
                index + 1
              }}</span>
            </div>
            <div class="text-gray-400 cursor-grab select-none" title="Перетащите для изменения порядка">
              ⋮⋮
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-900">
                {{ getLocationName(locationId) }}
              </p>
              <p class="text-xs text-gray-500">
                {{ getLocationAddress(locationId) }}
              </p>
            </div>
            <div class="flex items-center gap-1">
              <button
                type="button"
                class="w-7 h-7 rounded border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                :disabled="isUpdatingMetrics || index === 0"
                @click="$emit('move-location', { index, direction: -1 })"
              >
                ↑
              </button>
              <button
                type="button"
                class="w-7 h-7 rounded border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                :disabled="isUpdatingMetrics || index === result.locations.length - 1"
                @click="$emit('move-location', { index, direction: 1 })"
              >
                ↓
              </button>
            </div>
            <div class="text-sm text-gray-500">
              {{ getLocationTimeWindow(locationId) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Карта маршрута -->
      <div v-if="mapPoints.length >= 2" class="px-6 py-5">
        <h4 class="text-sm font-medium text-gray-900 mb-3">Карта маршрута</h4>
        <RouteMap :points="mapPoints" height="22rem" />
      </div>

      <!-- Actions -->
      <div class="px-6 py-4 bg-gray-50 flex justify-end space-x-3">
        <button
          @click="$emit('save')"
          :disabled="isUpdatingMetrics"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          {{ llmEvaluationStatus === 'current' ? 'Сохранить маршрут' : 'Сохранить без LLM-оценки' }}
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
import { computed, ref } from 'vue'
import type { Route } from '@/services/types'
import RouteMap, { type RoutePoint } from '@/components/RouteMap.vue'

const props = defineProps<{
  result: Route | null
  isLoading: boolean
  error: string | null
  routeSource?: 'original' | 'ai' | 'manual'
  routeLabel?: string | null
  isUpdatingMetrics?: boolean
  originalMetrics?: {
    total_distance_km: number
    total_time_hours: number
    total_cost_rub: number
  } | null
  originalLocationIds?: string[]
  canRestoreOriginal?: boolean
  canRestoreAi?: boolean
  aiRouteLabel?: string | null
  originalRouteSource?: string | null
  originalTrafficLightsCount?: number | null
  currentRouteSource?: string | null
  currentTrafficLightsCount?: number | null
  llmEvaluationStatus?: 'current' | 'stale' | 'unavailable'
  llmQualityScore?: number | null
  locations: Array<{
    id: string
    name: string
    address: string
    lat: number
    lon: number
    time_window_start: string
    time_window_end: string
  }>
}>()

const emit = defineEmits<{
  reset: []
  retry: []
  save: []
  'move-location': [{ index: number; direction: -1 | 1 }]
  'reorder-locations': [{ fromIndex: number; toIndex: number }]
  'restore-original': []
  'restore-ai': []
}>()

const dragFromIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

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

const routeSourceLabel = computed(() => {
  if (props.routeSource === 'manual') return 'Ручной порядок'
  if (props.routeSource === 'ai') return 'Вариант ИИ'
  return 'Исходный порядок'
})

const routeSourceBadgeClass = computed(() => {
  if (props.routeSource === 'manual') return 'bg-amber-100 text-amber-700'
  if (props.routeSource === 'ai') return 'bg-blue-100 text-blue-700'
  return 'bg-gray-100 text-gray-700'
})

const originalLocationIds = computed(() => props.originalLocationIds ?? [])

const llmStatusLabel = computed(() => {
  if (props.llmEvaluationStatus === 'current' && props.llmQualityScore !== null && props.llmQualityScore !== undefined) {
    return `LLM: ${props.llmQualityScore.toFixed(0)}/100`
  }
  if (props.llmEvaluationStatus === 'stale') {
    return 'LLM-оценка неактуальна'
  }
  return 'LLM-оценка не рассчитана'
})

const llmStatusBadgeClass = computed(() => {
  if (props.llmEvaluationStatus === 'current') return 'bg-emerald-100 text-emerald-700'
  if (props.llmEvaluationStatus === 'stale') return 'bg-amber-100 text-amber-700'
  return 'bg-gray-100 text-gray-700'
})

// Точки маршрута для карты (присоединяем lat/lon к result.locations по ID)
const mapPoints = computed<RoutePoint[]>(() => {
  if (!props.result || !props.locations?.length) return []
  return buildMapPoints(props.result.locations)
})

const originalMapPoints = computed<RoutePoint[]>(() => {
  if (!props.locations?.length || !originalLocationIds.value.length) return []
  return buildMapPoints(originalLocationIds.value)
})

const originalMetricsLabel = computed(() => {
  if (!props.originalMetrics) return 'Метрики исходного маршрута недоступны'
  return formatMetrics(
    props.originalMetrics.total_distance_km,
    props.originalMetrics.total_time_hours,
    props.originalMetrics.total_cost_rub
  )
})

const currentMetricsLabel = computed(() => {
  if (!props.result) return '—'
  return formatMetrics(
    props.result.total_distance_km,
    props.result.total_time_hours,
    props.result.total_cost_rub
  )
})

const originalRouteHint = computed(() =>
  buildRouteHint(props.originalRouteSource, props.originalTrafficLightsCount)
)

const currentRouteHint = computed(() =>
  buildRouteHint(props.currentRouteSource, props.currentTrafficLightsCount)
)

const originalRouteWarning = computed(() =>
  buildRouteWarning(props.originalRouteSource)
)

const currentRouteWarning = computed(() =>
  buildRouteWarning(props.currentRouteSource)
)

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

function buildMapPoints(locationIds: string[]): RoutePoint[] {
  const byId = new Map(props.locations.map((location) => [location.id, location]))
  const points: RoutePoint[] = []
  locationIds.forEach((id, index) => {
    const location = byId.get(id)
    if (location && Number.isFinite(location.lat) && Number.isFinite(location.lon)) {
      points.push({
        id,
        name: location.name,
        address: location.address,
        lat: location.lat,
        lon: location.lon,
        order: index + 1,
      })
    }
  })
  return points
}

function formatMetrics(distanceKm: number, timeHours: number, costRub: number): string {
  return `${distanceKm.toFixed(1)} км · ${timeHours.toFixed(1)} ч · ${costRub.toFixed(0)} ₽`
}

function buildRouteHint(source?: string | null, trafficLightsCount?: number | null): string | null {
  if (!source) return null
  if (source === 'road_network') {
    return trafficLightsCount && trafficLightsCount > 0
      ? `Маршрут по дорогам, учтено светофоров: ${trafficLightsCount}.`
      : 'Маршрут построен по дорожной сети.'
  }
  if (source === 'fallback') {
    return 'Маршрут оценён эвристически: дорожный сервис недоступен.'
  }
  if (source === 'client_fallback') {
    return 'Маршрут оценён приближённо на клиенте из-за ошибки preview.'
  }
  return null
}

function buildRouteWarning(source?: string | null): string | null {
  if (source === 'fallback') {
    return 'метрики примерные, потому что серверный дорожный роутинг был недоступен.'
  }
  if (source === 'client_fallback') {
    return 'метрики примерные, потому что не удалось получить маршрут по дорогам.'
  }
  return null
}

function onDragStart(index: number, event: DragEvent) {
  dragFromIndex.value = index
  dragOverIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
}

function onDragEnter(index: number) {
  if (dragFromIndex.value === null) return
  dragOverIndex.value = index
}

function onDrop(index: number) {
  if (dragFromIndex.value === null) return
  const fromIndex = dragFromIndex.value
  dragFromIndex.value = null
  dragOverIndex.value = null
  if (fromIndex === index) return
  emit('reorder-locations', { fromIndex, toIndex: index })
}

function onDragEnd() {
  dragFromIndex.value = null
  dragOverIndex.value = null
}
</script>
