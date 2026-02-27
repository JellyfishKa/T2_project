<template>
  <div>
    <!-- Заголовок -->
    <div class="mb-6">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
          <svg class="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        </div>
        <h2 class="text-xl font-bold text-gray-900">Выберите вариант маршрута</h2>
      </div>
      <div class="flex items-center justify-between">
        <p class="text-sm text-gray-500">
          Сгенерировано {{ variants.length }} варианта.
          <span v-if="llmEvaluationSuccess" class="text-green-600 font-medium">
            Модель {{ modelLabel }} оценила каждый вариант.
          </span>
          <span v-else class="text-amber-600">
            Оценка модели недоступна — показаны только метрики.
          </span>
        </p>
        <span class="text-xs text-gray-400">{{ responseTime }}мс</span>
      </div>
    </div>

    <!-- Карточки вариантов -->
    <div class="space-y-4">
      <div
        v-for="variant in variants"
        :key="variant.id"
        @click="selectVariant(variant)"
        class="bg-white rounded-xl border-2 cursor-pointer transition-all duration-200 hover:shadow-md"
        :class="
          selectedId === variant.id
            ? 'border-blue-500 shadow-md'
            : 'border-gray-200 hover:border-gray-300'
        "
      >
        <!-- Верхняя полоса с цветом варианта -->
        <div
          class="h-1.5 rounded-t-xl"
          :class="variantAccentColor(variant.id)"
        />

        <div class="p-5">
          <!-- Заголовок карточки -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div
                class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 text-sm font-bold"
                :class="variantBadgeClass(variant.id)"
              >
                {{ variant.id }}
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 leading-tight">{{ variant.name }}</h3>
                <p class="text-xs text-gray-500 mt-0.5">{{ variant.description }}</p>
              </div>
            </div>

            <!-- Чекбокс выбора -->
            <div
              class="w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all"
              :class="
                selectedId === variant.id
                  ? 'bg-blue-500 border-blue-500'
                  : 'border-gray-300'
              "
            >
              <svg
                v-if="selectedId === variant.id"
                class="w-3.5 h-3.5 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="3"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>

          <!-- Метрики -->
          <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="text-center p-2.5 bg-gray-50 rounded-lg">
              <div class="text-lg font-bold text-gray-900 tabular-nums">
                {{ variant.metrics.distance_km.toFixed(1) }}
              </div>
              <div class="text-xs text-gray-500 mt-0.5">км</div>
            </div>
            <div class="text-center p-2.5 bg-gray-50 rounded-lg">
              <div class="text-lg font-bold text-gray-900 tabular-nums">
                {{ formatTime(variant.metrics.time_hours) }}
              </div>
              <div class="text-xs text-gray-500 mt-0.5">время</div>
            </div>
            <div class="text-center p-2.5 bg-gray-50 rounded-lg">
              <div class="text-lg font-bold text-gray-900 tabular-nums">
                {{ Math.round(variant.metrics.cost_rub) }}
              </div>
              <div class="text-xs text-gray-500 mt-0.5">₽</div>
            </div>
          </div>

          <!-- Качество (полоса) -->
          <div class="mb-4">
            <div class="flex justify-between text-xs text-gray-500 mb-1">
              <span>Качество маршрута</span>
              <span class="font-medium" :class="qualityColor(variant.metrics.quality_score)">
                {{ variant.metrics.quality_score.toFixed(0) }}/100
              </span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-1.5">
              <div
                class="h-1.5 rounded-full transition-all duration-500"
                :class="qualityBarColor(variant.metrics.quality_score)"
                :style="{ width: `${Math.max(variant.metrics.quality_score, 2)}%` }"
              />
            </div>
          </div>

          <!-- Плюсы / Минусы от LLM -->
          <div
            v-if="variant.pros.length || variant.cons.length"
            class="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100"
          >
            <!-- Плюсы -->
            <div v-if="variant.pros.length">
              <p class="text-xs font-semibold text-green-700 mb-1.5 flex items-center gap-1">
                <span class="text-green-500">+</span> Преимущества
              </p>
              <ul class="space-y-1">
                <li
                  v-for="(pro, i) in variant.pros"
                  :key="i"
                  class="text-xs text-gray-600 flex items-start gap-1"
                >
                  <span class="text-green-400 mt-0.5 flex-shrink-0">•</span>
                  <span>{{ pro }}</span>
                </li>
              </ul>
            </div>

            <!-- Минусы -->
            <div v-if="variant.cons.length">
              <p class="text-xs font-semibold text-red-700 mb-1.5 flex items-center gap-1">
                <span class="text-red-500">−</span> Недостатки
              </p>
              <ul class="space-y-1">
                <li
                  v-for="(con, i) in variant.cons"
                  :key="i"
                  class="text-xs text-gray-600 flex items-start gap-1"
                >
                  <span class="text-red-400 mt-0.5 flex-shrink-0">•</span>
                  <span>{{ con }}</span>
                </li>
              </ul>
            </div>
          </div>

          <!-- Нет LLM-оценки -->
          <div
            v-else
            class="pt-3 border-t border-gray-100"
          >
            <p class="text-xs text-gray-400 italic text-center">
              Оценка модели не получена
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Кнопки действий -->
    <div class="mt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
      <button
        type="button"
        @click="$emit('reset')"
        class="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
      >
        Начать заново
      </button>

      <button
        type="button"
        @click="confirmSelection"
        :disabled="selectedId === null"
        class="w-full sm:w-auto px-6 py-2 rounded-lg text-sm font-medium text-white transition-colors"
        :class="
          selectedId !== null
            ? 'bg-blue-600 hover:bg-blue-700'
            : 'bg-gray-300 cursor-not-allowed'
        "
      >
        <span v-if="selectedId !== null">
          Применить вариант {{ selectedId }}
        </span>
        <span v-else>Выберите вариант</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RouteVariant } from '@/services/types'

const props = defineProps<{
  variants: RouteVariant[]
  modelUsed: string
  llmEvaluationSuccess: boolean
  responseTimeMs: number
}>()

const emit = defineEmits<{
  select: [variant: RouteVariant]
  reset: []
}>()

const selectedId = ref<number | null>(null)

// ─── Вычисляемые ──────────────────────────────────────────────────────────────
const modelLabel = computed(() =>
  props.modelUsed === 'qwen' ? 'Qwen' : 'Llama'
)

const responseTime = computed(() =>
  props.responseTimeMs > 1000
    ? `${(props.responseTimeMs / 1000).toFixed(1)}с`
    : `${props.responseTimeMs}мс`
)

// ─── Выбор варианта ───────────────────────────────────────────────────────────
function selectVariant(variant: RouteVariant) {
  selectedId.value = variant.id
}

function confirmSelection() {
  if (selectedId.value === null) return
  const variant = props.variants.find(v => v.id === selectedId.value)
  if (variant) {
    emit('select', variant)
  }
}

// ─── Стили ────────────────────────────────────────────────────────────────────
function variantAccentColor(id: number): string {
  return ['bg-blue-500', 'bg-emerald-500', 'bg-violet-500'][id - 1] ?? 'bg-gray-400'
}

function variantBadgeClass(id: number): string {
  return [
    'bg-blue-100 text-blue-700',
    'bg-emerald-100 text-emerald-700',
    'bg-violet-100 text-violet-700',
  ][id - 1] ?? 'bg-gray-100 text-gray-700'
}

function qualityColor(score: number): string {
  if (score >= 70) return 'text-green-600'
  if (score >= 40) return 'text-amber-600'
  return 'text-red-600'
}

function qualityBarColor(score: number): string {
  if (score >= 70) return 'bg-green-500'
  if (score >= 40) return 'bg-amber-500'
  return 'bg-red-500'
}

// ─── Утилиты ──────────────────────────────────────────────────────────────────
function formatTime(hours: number): string {
  const h = Math.floor(hours)
  const m = Math.round((hours - h) * 60)
  if (h === 0) return `${m}мин`
  if (m === 0) return `${h}ч`
  return `${h}ч ${m}м`
}
</script>
