<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
    <!-- Заголовок -->
    <div class="text-center mb-8">
      <div
        class="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4"
      >
        <svg
          class="animate-spin w-8 h-8 text-blue-600"
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
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Генерация вариантов маршрута</h2>
      <p class="text-sm text-gray-500 mt-1">
        Модель
        <span class="font-semibold" :class="modelLabelColor">{{ modelLabel }}</span>
        анализирует точки и формирует варианты...
      </p>
    </div>

    <!-- Прогресс-бар -->
    <div class="mb-8">
      <div class="flex justify-between text-sm text-gray-600 mb-2">
        <span class="font-medium">{{ currentStepLabel }}</span>
        <span class="tabular-nums">{{ Math.round(displayProgress) }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          class="h-3 rounded-full transition-all duration-700 ease-out"
          :class="done ? 'bg-green-500' : 'bg-blue-600'"
          :style="{ width: `${displayProgress}%` }"
        />
      </div>
    </div>

    <!-- Список шагов -->
    <div class="space-y-3">
      <div
        v-for="(step, i) in steps"
        :key="i"
        class="flex items-center gap-3"
      >
        <!-- Иконка состояния -->
        <div class="flex-shrink-0">
          <div
            v-if="i < currentStepIndex"
            class="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center"
          >
            <svg class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div
            v-else-if="i === currentStepIndex"
            class="w-6 h-6 border-2 border-blue-500 rounded-full flex items-center justify-center"
          >
            <div class="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse" />
          </div>
          <div
            v-else
            class="w-6 h-6 bg-gray-200 rounded-full"
          />
        </div>

        <!-- Текст шага -->
        <span
          class="text-sm transition-colors duration-300"
          :class="
            i < currentStepIndex
              ? 'text-green-700 font-medium'
              : i === currentStepIndex
                ? 'text-blue-700 font-semibold'
                : 'text-gray-400'
          "
        >
          {{ step.label }}
        </span>

        <!-- Время (только для текущего) -->
        <span
          v-if="i === currentStepIndex"
          class="ml-auto text-xs text-gray-400 tabular-nums"
        >
          {{ elapsedLabel }}
        </span>
      </div>
    </div>

    <!-- Подсказка -->
    <p class="mt-6 text-xs text-center text-gray-400">
      Это может занять 30–120 секунд в зависимости от числа точек
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

interface Step {
  label: string
  targetProgress: number  // прогресс по достижении этого шага (%)
  minDuration: number     // минимальное время на шаге (секунды)
}

const props = defineProps<{
  model: string   // 'qwen' | 'llama'
  done: boolean   // true когда API ответил
}>()

// ─── Данные о шагах ────────────────────────────────────────────────────────────
const steps: Step[] = [
  { label: 'Подготовка данных и точек маршрута',    targetProgress: 15, minDuration: 2  },
  { label: 'Расчёт трёх вариантов маршрута',        targetProgress: 30, minDuration: 3  },
  { label: 'Анализ вариантов языковой моделью',     targetProgress: 88, minDuration: 30 },
  { label: 'Формирование и проверка результатов',   targetProgress: 100, minDuration: 1 },
]

// ─── Состояние ────────────────────────────────────────────────────────────────
const rawProgress   = ref(0)
const displayProgress = ref(0)
const currentStepIndex = ref(0)
const elapsedSeconds  = ref(0)

let tickInterval: ReturnType<typeof setInterval> | null = null
let elapsedInterval: ReturnType<typeof setInterval> | null = null

// ─── Вычисляемые ──────────────────────────────────────────────────────────────
const currentStepLabel = computed(
  () => steps[currentStepIndex.value]?.label ?? 'Завершение...'
)

const modelLabel = computed(() =>
  props.model === 'qwen' ? 'Qwen' : 'Llama'
)

const modelLabelColor = computed(() =>
  props.model === 'qwen' ? 'text-purple-600' : 'text-green-600'
)

const elapsedLabel = computed(() => {
  const m = Math.floor(elapsedSeconds.value / 60)
  const s = elapsedSeconds.value % 60
  return m > 0
    ? `${m}мин ${s.toString().padStart(2, '0')}с`
    : `${s}с`
})

// ─── Логика прогресса ─────────────────────────────────────────────────────────
const TICK_MS = 500

function getIncrement(): number {
  const step = steps[currentStepIndex.value]
  if (!step) return 0.3

  const range = step.targetProgress - (steps[currentStepIndex.value - 1]?.targetProgress ?? 0)
  const minTicks = (step.minDuration * 1000) / TICK_MS

  // Если LLM-шаг (индекс 2), идём очень медленно
  return currentStepIndex.value === 2
    ? Math.min(range / minTicks, 0.6)
    : range / minTicks
}

function tick() {
  if (props.done) {
    rawProgress.value = 100
    displayProgress.value = 100
    currentStepIndex.value = steps.length - 1
    stopTick()
    return
  }

  const currentTarget = steps[currentStepIndex.value]?.targetProgress ?? 88
  const increment = getIncrement()

  rawProgress.value = Math.min(rawProgress.value + increment, currentTarget)
  displayProgress.value = rawProgress.value

  // Переходим к следующему шагу когда почти достигли цели
  if (
    rawProgress.value >= currentTarget - 0.5 &&
    currentStepIndex.value < steps.length - 2
  ) {
    currentStepIndex.value++
  }
}

function stopTick() {
  if (tickInterval) {
    clearInterval(tickInterval)
    tickInterval = null
  }
  if (elapsedInterval) {
    clearInterval(elapsedInterval)
    elapsedInterval = null
  }
}

// Когда API ответил — плавно доводим до 100%
watch(() => props.done, (isDone) => {
  if (isDone) {
    rawProgress.value = 100
    currentStepIndex.value = steps.length - 1
    // Плавная анимация через RAF
    const animate = () => {
      if (displayProgress.value < 100) {
        displayProgress.value = Math.min(displayProgress.value + 3, 100)
        requestAnimationFrame(animate)
      }
    }
    requestAnimationFrame(animate)
    stopTick()
  }
})

onMounted(() => {
  rawProgress.value = 0
  displayProgress.value = 0
  currentStepIndex.value = 0
  elapsedSeconds.value = 0

  tickInterval = setInterval(tick, TICK_MS)
  elapsedInterval = setInterval(() => { elapsedSeconds.value++ }, 1000)
})

onUnmounted(() => {
  stopTick()
})
</script>
