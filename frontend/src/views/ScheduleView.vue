<template>
  <div class="schedule-view p-6">
    <!-- Заголовок и фильтры -->
    <div class="flex flex-wrap items-center gap-4 mb-6">
      <h1 class="text-2xl font-bold flex-1">Расписание маршрутов</h1>

      <div class="flex items-center gap-2">
        <button class="btn-icon" @click="shiftMonth(-1)">◀</button>
        <span class="font-medium min-w-[8rem] text-center">{{ monthLabel }}</span>
        <button class="btn-icon" @click="shiftMonth(1)">▶</button>
      </div>

      <button class="btn-primary" @click="showGenerate = true">Сгенерировать план</button>
      <button class="btn-secondary" @click="showFM = true">Форс-мажор</button>
    </div>

    <!-- Легенда категорий -->
    <div class="flex gap-3 mb-4 text-sm">
      <span v-for="cat in ['A','B','C','D']" :key="cat" class="flex items-center gap-1">
        <span :class="catDot(cat)"></span>{{ cat }}
      </span>
    </div>

    <!-- Загрузка / ошибка -->
    <div v-if="loading" class="text-gray-400">Загрузка расписания…</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <!-- Таблица по дням -->
    <div v-else class="space-y-2">
      <div
        v-for="route in sortedRoutes"
        :key="route.rep_id + route.date"
        class="card p-3"
      >
        <div class="flex items-center gap-3 mb-2">
          <span class="font-medium text-sm">{{ route.date }}</span>
          <span class="text-blue-400 font-medium">{{ route.rep_name }}</span>
          <span class="text-gray-400 text-xs">{{ route.total_tt }} ТТ · ~{{ route.estimated_duration_hours }}ч</span>
        </div>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="visit in route.visits"
            :key="visit.id"
            :class="catBadge(visit.location_category)"
            :title="`${visit.location_name} [${visit.location_category}] — ${visit.status}`"
            class="visit-chip"
          >
            {{ visit.location_category }} · {{ visit.location_name.slice(0, 20) }}
          </span>
        </div>
      </div>
      <div v-if="!sortedRoutes.length" class="text-gray-500 text-sm">
        Нет маршрутов за {{ monthLabel }}. Нажмите «Сгенерировать план».
      </div>
    </div>

    <!-- Модал: генерация плана -->
    <div v-if="showGenerate" class="modal-overlay" @click.self="showGenerate = false">
      <div class="modal">
        <h2 class="font-semibold text-lg mb-4">Сгенерировать план</h2>
        <p class="text-sm text-gray-400 mb-4">
          Месяц: <strong>{{ currentMonth }}</strong><br>
          Будут сгенерированы маршруты для всех активных сотрудников на основе категорий ТТ.
        </p>
        <div class="flex gap-3 justify-end">
          <button class="btn-secondary" @click="showGenerate = false">Отмена</button>
          <button class="btn-primary" :disabled="generating" @click="generatePlan">
            {{ generating ? 'Генерация…' : 'Сгенерировать' }}
          </button>
        </div>
        <div v-if="genResult" class="mt-3 text-sm text-green-400">{{ genResult }}</div>
      </div>
    </div>

    <!-- Модал: форс-мажор -->
    <div v-if="showFM" class="modal-overlay" @click.self="showFM = false">
      <div class="modal">
        <h2 class="font-semibold text-lg mb-4">Форс-мажор</h2>
        <div class="space-y-3">
          <div>
            <label class="label">Тип</label>
            <select v-model="fm.type" class="input">
              <option value="illness">Болезнь</option>
              <option value="weather">Погодные условия</option>
              <option value="vehicle_breakdown">Неисправность ТС</option>
              <option value="other">Другое</option>
            </select>
          </div>
          <div>
            <label class="label">Сотрудник</label>
            <select v-model="fm.rep_id" class="input">
              <option v-for="r in reps" :key="r.id" :value="r.id">{{ r.name }}</option>
            </select>
          </div>
          <div>
            <label class="label">Дата инцидента</label>
            <input v-model="fm.event_date" type="date" class="input" />
          </div>
          <div>
            <label class="label">Описание</label>
            <textarea v-model="fm.description" class="input" rows="2" />
          </div>
        </div>
        <div class="flex gap-3 justify-end mt-4">
          <button class="btn-secondary" @click="showFM = false">Отмена</button>
          <button class="btn-primary" :disabled="submittingFM" @click="submitFM">
            {{ submittingFM ? 'Обработка…' : 'Зафиксировать' }}
          </button>
        </div>
        <div v-if="fmResult" class="mt-3 text-sm text-green-400 whitespace-pre-line">{{ fmResult }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { DailyRoute, SalesRep } from '@/services/types'

const API = '/api/v1'

// ─── State ───────────────────────────────────────────────────────────────────
const today = new Date()
const monthOffset = ref(0)
const routes = ref<DailyRoute[]>([])
const reps = ref<SalesRep[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showGenerate = ref(false)
const showFM = ref(false)
const generating = ref(false)
const genResult = ref<string | null>(null)
const submittingFM = ref(false)
const fmResult = ref<string | null>(null)

const fm = ref({
  type: 'illness' as string,
  rep_id: '',
  event_date: '',
  description: '',
})

// ─── Computed ─────────────────────────────────────────────────────────────────
const currentMonth = computed(() => {
  const d = new Date(today.getFullYear(), today.getMonth() + monthOffset.value, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
})

const monthLabel = computed(() => {
  const [y, m] = currentMonth.value.split('-')
  const names = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                 'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
  return `${names[Number(m) - 1]} ${y}`
})

const sortedRoutes = computed(() =>
  [...routes.value].sort((a, b) => a.date.localeCompare(b.date) || a.rep_name.localeCompare(b.rep_name))
)

// ─── Methods ──────────────────────────────────────────────────────────────────
function shiftMonth(delta: number) {
  monthOffset.value += delta
  loadSchedule()
}

async function loadSchedule() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`${API}/schedule/?month=${currentMonth.value}`)
    if (!res.ok) throw new Error(await res.text())
    const plan = await res.json()
    routes.value = plan.routes ?? []
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadReps() {
  const res = await fetch(`${API}/reps/`)
  reps.value = await res.json()
}

async function generatePlan() {
  generating.value = true
  genResult.value = null
  try {
    const res = await fetch(`${API}/schedule/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ month: currentMonth.value }),
    })
    const data = await res.json()
    genResult.value = `Готово: ${data.total_visits_planned} визитов, ${data.total_tt_planned} ТТ, охват ${data.coverage_pct}%`
    await loadSchedule()
  } catch (e: any) {
    genResult.value = `Ошибка: ${e.message}`
  } finally {
    generating.value = false
  }
}

async function submitFM() {
  submittingFM.value = true
  fmResult.value = null
  try {
    const res = await fetch(`${API}/force_majeure/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fm.value),
    })
    const data = await res.json()
    fmResult.value = `Зафиксировано. Перераспределено ${data.affected_tt_count} ТТ.`
    await loadSchedule()
  } catch (e: any) {
    fmResult.value = `Ошибка: ${e.message}`
  } finally {
    submittingFM.value = false
  }
}

// ─── Category styling ─────────────────────────────────────────────────────────
function catDot(cat: string) {
  return `w-3 h-3 rounded-full ${catColor(cat)}`
}
function catBadge(cat: string | null) {
  return `${catColor(cat ?? '?')} text-white`
}
function catColor(cat: string) {
  return { A: 'bg-red-600', B: 'bg-orange-500', C: 'bg-yellow-500', D: 'bg-gray-500' }[cat] ?? 'bg-gray-600'
}

onMounted(() => {
  loadSchedule()
  loadReps()
})
</script>

<style scoped>
.card { @apply bg-gray-800 rounded-lg border border-gray-700; }
.input { @apply bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm text-white w-full; }
.label { @apply block text-xs text-gray-400 mb-1; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded disabled:opacity-50; }
.btn-secondary { @apply bg-gray-600 hover:bg-gray-500 text-white text-sm px-4 py-2 rounded; }
.btn-icon { @apply bg-gray-700 hover:bg-gray-600 text-white w-8 h-8 rounded flex items-center justify-center; }
.visit-chip { @apply text-xs px-2 py-0.5 rounded-full cursor-default; }
.modal-overlay { @apply fixed inset-0 bg-black/60 flex items-center justify-center z-50; }
.modal { @apply bg-gray-800 border border-gray-600 rounded-lg p-6 w-full max-w-md; }
</style>
