<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4"
    role="dialog"
    aria-modal="true"
    @click.self="$emit('close')"
  >
    <div class="w-full max-w-6xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl">
      <div class="flex items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Route Comparison</p>
          <h3 class="mt-1 text-2xl font-semibold text-slate-900">Сравнение маршрута</h3>
          <p class="mt-1 text-sm text-slate-600">
            {{ routeName || 'Маршрут' }}
            <span v-if="comparison?.created_at"> · {{ formatDateTime(comparison.created_at) }}</span>
          </p>
        </div>
        <button
          type="button"
          class="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          @click="$emit('close')"
        >
          Закрыть
        </button>
      </div>

      <div class="px-6 py-6">
        <div v-if="isLoading" class="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
          <div class="h-96 animate-pulse rounded-2xl bg-slate-100" />
          <div class="space-y-4">
            <div class="h-28 animate-pulse rounded-2xl bg-slate-100" />
            <div class="h-64 animate-pulse rounded-2xl bg-slate-100" />
          </div>
        </div>

        <div
          v-else-if="error"
          class="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800"
        >
          {{ error }}
        </div>

        <div
          v-else-if="!comparison"
          class="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4 text-sm text-slate-600"
        >
          История сравнения для этого маршрута пока недоступна.
        </div>

        <template v-else>
          <div class="mb-6 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <div
              v-for="item in summaryCards"
              :key="item.label"
              class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4"
            >
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{{ item.label }}</p>
              <p class="mt-2 text-xl font-semibold" :class="item.valueClass">{{ item.value }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ item.hint }}</p>
            </div>
          </div>

          <div class="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(340px,0.85fr)]">
            <div class="space-y-4">
              <div class="flex flex-wrap gap-2">
                <span class="inline-flex items-center rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  <span class="mr-2 h-2.5 w-2.5 rounded-full bg-slate-400" />
                  До оптимизации
                </span>
                <span class="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                  <span class="mr-2 h-2.5 w-2.5 rounded-full bg-blue-500" />
                  После оптимизации
                </span>
              </div>
              <RouteMap :routes="routeSets" height="28rem" />
            </div>

            <div class="grid gap-4 lg:grid-cols-2 xl:grid-cols-1">
              <section class="rounded-2xl border border-slate-200 bg-white">
                <div class="border-b border-slate-100 px-4 py-3">
                  <h4 class="text-sm font-semibold text-slate-900">Исходный порядок</h4>
                  <p class="mt-1 text-xs text-slate-500">Позиции до последней оптимизации</p>
                </div>
                <div class="max-h-[22rem] space-y-2 overflow-y-auto px-4 py-4">
                  <div
                    v-for="point in comparison.original"
                    :key="`original-${point.id}`"
                    class="flex items-start gap-3 rounded-2xl border border-slate-200 px-3 py-3"
                  >
                    <div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-700">
                      {{ point.order }}
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="truncate text-sm font-medium text-slate-900">{{ point.name }}</p>
                      <p v-if="point.address" class="truncate text-xs text-slate-500">{{ point.address }}</p>
                    </div>
                    <span
                      v-if="getShiftLabel(point.id, 'original')"
                      class="inline-flex flex-shrink-0 rounded-full px-2 py-1 text-xs font-medium"
                      :class="getShiftClass(point.id, 'original')"
                    >
                      {{ getShiftLabel(point.id, 'original') }}
                    </span>
                  </div>
                </div>
              </section>

              <section class="rounded-2xl border border-slate-200 bg-white">
                <div class="border-b border-slate-100 px-4 py-3">
                  <h4 class="text-sm font-semibold text-slate-900">Текущий порядок</h4>
                  <p class="mt-1 text-xs text-slate-500">Позиции после сохранённой оптимизации</p>
                </div>
                <div class="max-h-[22rem] space-y-2 overflow-y-auto px-4 py-4">
                  <div
                    v-for="point in comparison.current"
                    :key="`current-${point.id}`"
                    class="flex items-start gap-3 rounded-2xl border border-blue-100 bg-blue-50/40 px-3 py-3"
                  >
                    <div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700">
                      {{ point.order }}
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="truncate text-sm font-medium text-slate-900">{{ point.name }}</p>
                      <p v-if="point.address" class="truncate text-xs text-slate-500">{{ point.address }}</p>
                    </div>
                    <span
                      v-if="getShiftLabel(point.id, 'current')"
                      class="inline-flex flex-shrink-0 rounded-full px-2 py-1 text-xs font-medium"
                      :class="getShiftClass(point.id, 'current')"
                    >
                      {{ getShiftLabel(point.id, 'current') }}
                    </span>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import RouteMap, { type RouteSet } from '@/components/RouteMap.vue'
import type { RouteComparison } from '@/services/types'

const props = defineProps<{
  open: boolean
  comparison?: RouteComparison | null
  routeName?: string | null
  isLoading?: boolean
  error?: string | null
}>()

defineEmits<{
  close: []
}>()

const originalOrderMap = computed(() =>
  new Map((props.comparison?.original ?? []).map((point) => [point.id, point.order]))
)

const currentOrderMap = computed(() =>
  new Map((props.comparison?.current ?? []).map((point) => [point.id, point.order]))
)

const routeSets = computed<RouteSet[]>(() => {
  if (!props.comparison) return []

  return [
    {
      id: 'original',
      color: '#94a3b8',
      points: props.comparison.original.map((point) => ({
        ...point,
        color: '#94a3b8',
      })),
      selected: false,
    },
    {
      id: 'current',
      color: '#3b82f6',
      points: props.comparison.current.map((point) => ({
        ...point,
        color: '#3b82f6',
      })),
      selected: true,
    },
  ]
})

const summaryCards = computed(() => {
  const diff = props.comparison?.diff
  if (!diff) return []

  return [
    {
      label: 'Δ км',
      value: formatDelta(diff.distance_delta_km, 'км', 1),
      valueClass: getDeltaValueClass(diff.distance_delta_km, 0.05),
      hint: getDeltaHint(diff.distance_delta_km, 'расстоянию', 0.05),
    },
    {
      label: 'Δ ч',
      value: formatDelta(diff.time_delta_hours, 'ч', 1),
      valueClass: getDeltaValueClass(diff.time_delta_hours, 0.05),
      hint: getDeltaHint(diff.time_delta_hours, 'времени', 0.05),
    },
    {
      label: 'Δ ₽',
      value: formatDelta(diff.cost_delta_rub, '₽', 0),
      valueClass: getDeltaValueClass(diff.cost_delta_rub, 0.5),
      hint: getDeltaHint(diff.cost_delta_rub, 'стоимости', 0.5),
    },
    {
      label: 'Изменено точек',
      value: `${diff.changed_stops_count}`,
      valueClass: 'text-slate-900',
      hint: 'Количество остановок с новой позицией или составом',
    },
    {
      label: 'Improvement',
      value: `${diff.improvement_percentage.toFixed(1)}%`,
      valueClass: 'text-blue-700',
      hint: 'Оценка улучшения из сохранённого результата оптимизации',
    },
  ]
})

function formatDateTime(value: string | null): string {
  if (!value) return '—'
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatDelta(value: number, unit: string, digits = 1): string {
  const threshold = digits === 0 ? 0.5 : 0.05
  if (Math.abs(value) < threshold) return `±0 ${unit}`
  const sign = value < 0 ? '−' : '+'
  return `${sign}${Math.abs(value).toFixed(digits)} ${unit}`
}

function getDeltaValueClass(value: number, threshold: number): string {
  if (Math.abs(value) < threshold) return 'text-slate-500'
  return value < 0 ? 'text-emerald-600' : 'text-rose-600'
}

function getDeltaHint(value: number, dimension: string, threshold: number): string {
  if (Math.abs(value) < threshold) return `Почти без изменений по ${dimension}`
  return value < 0 ? `Лучше по ${dimension}` : `Хуже по ${dimension}`
}

function getShiftLabel(pointId: string, side: 'original' | 'current'): string | null {
  const originalOrder = originalOrderMap.value.get(pointId)
  const currentOrder = currentOrderMap.value.get(pointId)

  if (side === 'current') {
    if (originalOrder === undefined) return 'Новая'
    const delta = currentOrder! - originalOrder
    if (delta === 0) return null
    return delta < 0 ? `↑${Math.abs(delta)}` : `↓${delta}`
  }

  if (currentOrder === undefined) return 'Убрана'
  const delta = currentOrder - originalOrder!
  if (delta === 0) return null
  return delta < 0 ? `↑${Math.abs(delta)}` : `↓${delta}`
}

function getShiftClass(pointId: string, side: 'original' | 'current'): string {
  const label = getShiftLabel(pointId, side)
  if (!label) return 'bg-slate-100 text-slate-600'
  if (label === 'Новая') return 'bg-blue-100 text-blue-700'
  if (label === 'Убрана') return 'bg-rose-100 text-rose-700'
  return label.startsWith('↑') ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
}
</script>
