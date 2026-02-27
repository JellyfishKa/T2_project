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
      <button
        class="btn-secondary flex items-center gap-1.5"
        :disabled="exportLoading"
        @click="handleExport"
        title="Скачать Excel с расписанием и аналитикой"
      >
        <svg v-if="exportLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
        </svg>
        <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
        </svg>
        <span>{{ exportLoading ? 'Экспорт…' : 'Excel' }}</span>
      </button>
    </div>

    <!-- Легенда категорий -->
    <div class="flex gap-3 mb-4 text-sm">
      <span v-for="cat in ['A','B','C','D']" :key="cat" class="flex items-center gap-1">
        <span :class="catDot(cat)"></span>{{ cat }}
      </span>
      <span class="flex items-center gap-2 ml-4">
        <span class="w-3 h-3 rounded-full bg-green-600"></span><span class="text-green-400">выполнен</span>
        <span class="w-3 h-3 rounded-full bg-red-800 ml-2"></span><span class="text-red-400">пропущен</span>
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
        <div
          class="flex items-center gap-3 mb-2 cursor-pointer hover:text-blue-300 transition-colors"
          @click="openDayModal(route)"
        >
          <span class="font-medium text-sm">{{ route.date }}</span>
          <span class="text-blue-400 font-medium">{{ route.rep_name }}</span>
          <span class="text-gray-400 text-xs">
            {{ route.total_tt }} ТТ · ~{{ route.estimated_duration_hours }}ч
          </span>
          <span class="text-gray-600 text-xs ml-auto">↗ детали</span>
        </div>
        <div class="flex flex-wrap gap-1 items-center">
          <template v-for="(visit, idx) in route.visits" :key="visit.id">
            <!-- Разделитель обеда после 7-го визита -->
            <div
              v-if="route.lunch_break_at && idx === 7"
              class="w-full flex items-center gap-2 my-1 text-xs text-yellow-500"
            >
              <span>🍽</span>
              <span>Обед {{ route.lunch_break_at }}</span>
              <div class="flex-1 border-t border-yellow-700"></div>
            </div>
            <span
              :class="visitChipClass(visit)"
              :title="`${visit.location_name} [${visit.location_category ?? '?'}] — ${visit.status}${visit.time_in ? ' · вход ' + visit.time_in : ''}${visit.time_out ? ' · выход ' + visit.time_out : ''}`"
              class="visit-chip cursor-pointer hover:opacity-80"
              @click="openVisitModal(visit)"
            >
              {{ visit.location_category ?? '?' }} · {{ visit.location_name.slice(0, 18) }}
              <span v-if="visit.status === 'completed'">
                <span class="ml-0.5">✓</span>
                <span v-if="visitDuration(visit)" class="ml-0.5 opacity-75">{{ visitDuration(visit) }}м</span>
              </span>
              <span v-else-if="visit.status === 'skipped'" class="ml-0.5">✗</span>
            </span>
          </template>
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

    <!-- Модал: детальный просмотр дня + LLM оптимизация -->
    <div v-if="showDayModal && selectedDayRoute" class="modal-overlay" @click.self="showDayModal = false">
      <div class="modal" style="max-width: 540px;">
        <div class="flex items-start justify-between mb-4">
          <div>
            <h2 class="font-semibold text-lg">{{ selectedDayRoute.rep_name }}</h2>
            <p class="text-sm text-gray-400">
              {{ selectedDayRoute.date }} · {{ selectedDayRoute.total_tt }} ТТ
              · ~{{ selectedDayRoute.estimated_duration_hours }}ч
            </p>
          </div>
          <button class="btn-icon text-xs" @click="showDayModal = false">✕</button>
        </div>

        <!-- Список визитов дня -->
        <div class="space-y-0.5 mb-4 max-h-56 overflow-y-auto pr-1">
          <div
            v-for="(v, i) in selectedDayRoute.visits"
            :key="v.id"
            class="flex items-center gap-2 text-sm py-1 border-b border-gray-700"
          >
            <span class="text-gray-600 w-5 shrink-0">{{ i + 1 }}.</span>
            <span :class="catColor(v.location_category ?? '?')" class="visit-chip shrink-0 text-white">
              {{ v.location_category ?? '?' }}
            </span>
            <span class="flex-1 truncate text-xs">{{ v.location_name }}</span>
            <span v-if="v.time_in" class="text-xs text-gray-400 shrink-0">
              {{ v.time_in }}–{{ v.time_out ?? '?' }}
              <span v-if="visitDuration(v)" class="text-green-400 ml-0.5">({{ visitDuration(v) }}м)</span>
            </span>
            <span class="text-xs shrink-0" :class="statusColor(v.status)">{{ statusLabel(v.status) }}</span>
          </div>
        </div>

        <!-- Выбор модели + кнопка оптимизации -->
        <div class="border-t border-gray-700 pt-3 mt-1">
          <p class="text-xs text-gray-500 mb-2">Модель для оценки вариантов:</p>
          <div class="flex gap-2 mb-3">
            <button
              v-for="m in [{ id: 'qwen', label: 'Qwen 0.5B', hint: 'быстрая' }, { id: 'llama', label: 'Llama 1B', hint: 'точнее' }]"
              :key="m.id"
              class="flex-1 text-xs py-1.5 rounded font-medium transition-colors"
              :class="selectedModel === m.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
              :disabled="dayOptLoading"
              @click="selectedModel = (m.id as 'qwen' | 'llama')"
            >
              {{ m.label }}
              <span class="opacity-60 ml-1">({{ m.hint }})</span>
            </button>
          </div>

          <button
            class="btn-primary w-full flex items-center justify-center gap-2"
            :disabled="dayOptLoading"
            @click="optimizeDayRoute"
          >
            <svg v-if="dayOptLoading" class="animate-spin h-4 w-4 text-white flex-shrink-0" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>{{ dayOptLoading ? 'Строю варианты маршрута…' : 'Получить варианты (ИИ)' }}</span>
          </button>

          <!-- Прогресс-бар -->
          <div v-if="dayOptLoading" class="mt-2">
            <div class="relative w-full bg-gray-700 rounded-full h-1 overflow-hidden">
              <div class="absolute top-0 left-0 h-1 bg-blue-500 rounded-full animate-pulse w-full" />
            </div>
            <p class="text-xs text-gray-500 mt-1 text-center">
              Строю 3 варианта + оцениваю через {{ selectedModel === 'qwen' ? 'Qwen' : 'Llama' }}…
            </p>
          </div>
        </div>

        <div v-if="dayOptError" class="mt-2 text-sm text-red-400">{{ dayOptError }}</div>

        <!-- 3 варианта маршрута -->
        <div v-if="dayOptResult" class="mt-3 space-y-2">
          <div class="flex items-center gap-2 text-xs text-gray-400 mb-1">
            <span>Модель: <strong class="text-blue-300">{{ dayOptResult.model_used }}</strong></span>
            <span v-if="!dayOptResult.llm_evaluation_success" class="text-yellow-400 ml-1">
              · ИИ-оценка недоступна
            </span>
          </div>

          <div
            v-for="variant in dayOptResult.variants"
            :key="variant.id"
            class="rounded border p-3 cursor-pointer transition-all"
            :class="selectedVariantId === variant.id
              ? 'border-blue-500 bg-blue-900/20'
              : 'border-gray-600 bg-gray-900 hover:border-gray-500'"
            @click="selectedVariantId = variant.id"
          >
            <div class="flex items-start justify-between mb-1">
              <p class="text-sm font-medium text-white">{{ variant.name }}</p>
              <span class="text-xs px-1.5 py-0.5 rounded ml-2 flex-shrink-0"
                :class="variant.metrics.quality_score >= 80 ? 'bg-green-900 text-green-300' : 'bg-gray-700 text-gray-300'"
              >
                {{ variant.metrics.quality_score.toFixed(0) }}%
              </span>
            </div>
            <p class="text-xs text-gray-400 mb-2">{{ variant.description }}</p>
            <!-- Метрики -->
            <div class="flex gap-3 text-xs text-gray-300 mb-2">
              <span>📍 {{ variant.metrics.distance_km.toFixed(1) }} км</span>
              <span>⏱ {{ variant.metrics.time_hours.toFixed(1) }} ч</span>
              <span>💰 {{ variant.metrics.cost_rub.toFixed(0) }} ₽</span>
            </div>
            <!-- Pros / Cons -->
            <div v-if="variant.pros.length || variant.cons.length" class="flex flex-wrap gap-1">
              <span
                v-for="p in variant.pros" :key="'p'+p"
                class="text-xs bg-green-900/50 text-green-300 px-1.5 py-0.5 rounded"
              >✓ {{ p }}</span>
              <span
                v-for="c in variant.cons" :key="'c'+c"
                class="text-xs bg-red-900/40 text-red-300 px-1.5 py-0.5 rounded"
              >✗ {{ c }}</span>
            </div>
          </div>

          <!-- Сохранить выбранный -->
          <button
            v-if="selectedVariantId !== null"
            class="btn-primary w-full text-sm mt-1"
            :disabled="confirmingVariant"
            @click="confirmSelectedVariant"
          >
            {{ confirmingVariant ? 'Сохранение…' : 'Сохранить выбранный маршрут' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Модал: статус визита -->
    <div v-if="showVisitModal && selectedVisit" class="modal-overlay" @click.self="closeVisitModal">
      <div class="modal">
        <h2 class="font-semibold text-lg mb-1">Визит</h2>
        <p class="text-sm text-gray-300 mb-4">
          <span :class="catBadge(selectedVisit.location_category)" class="visit-chip mr-2">
            {{ selectedVisit.location_category ?? '?' }}
          </span>
          {{ selectedVisit.location_name }}
        </p>

        <!-- Сохранённое время (если уже было посещение) -->
        <p v-if="selectedVisit?.time_in" class="text-sm text-blue-300 mb-3">
          ⏱ {{ selectedVisit.time_in }} — {{ selectedVisit.time_out ?? '?' }}
          <span v-if="visitDuration(selectedVisit!)" class="ml-1 text-green-400">
            ({{ visitDuration(selectedVisit!) }} мин на точке)
          </span>
        </p>

        <!-- Кнопки статуса -->
        <div class="flex gap-2 mb-4">
          <button
            v-for="opt in statusOptions"
            :key="opt.value"
            :class="[opt.cls, visitForm.status === opt.value ? 'ring-2 ring-white' : 'opacity-70']"
            class="flex-1 text-sm py-1.5 rounded font-medium"
            @click="visitForm.status = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>

        <!-- Время (только для выполненного) -->
        <div v-if="visitForm.status === 'completed'" class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="label">Прибыл в</label>
            <input v-model="visitForm.time_in" type="time" class="input" />
          </div>
          <div>
            <label class="label">Ушёл в</label>
            <input v-model="visitForm.time_out" type="time" class="input" />
          </div>
        </div>

        <!-- Заметки -->
        <div class="mb-4">
          <label class="label">Заметки</label>
          <textarea v-model="visitForm.notes" class="input" rows="2"
            placeholder="Причина пропуска, комментарий…" />
        </div>

        <div class="flex gap-3 justify-end">
          <button class="btn-secondary" @click="closeVisitModal">Отмена</button>
          <button class="btn-primary" :disabled="savingVisit" @click="submitVisitUpdate">
            {{ savingVisit ? 'Сохранение…' : 'Сохранить' }}
          </button>
        </div>
        <div v-if="visitError" class="mt-2 text-sm text-red-400">{{ visitError }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { DailyRoute, OptimizeVariantsResponse, ConfirmVariantRequest, SalesRep, VisitScheduleItem } from '@/services/types'
import { optimizeVariants, confirmVariant, updateVisitStatus, downloadScheduleExcel } from '@/services/api'

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
const exportLoading = ref(false)
const generating = ref(false)
const genResult = ref<string | null>(null)
const submittingFM = ref(false)
const fmResult = ref<string | null>(null)

// ─── Visit modal state ────────────────────────────────────────────────────────
const showVisitModal = ref(false)
const selectedVisit = ref<VisitScheduleItem | null>(null)
const savingVisit = ref(false)
const visitError = ref<string | null>(null)
const visitForm = ref({
  status: 'planned' as VisitScheduleItem['status'],
  time_in: '',
  time_out: '',
  notes: '',
})

const statusOptions = [
  { value: 'completed' as const, label: '✓ Выполнен', cls: 'bg-green-700 hover:bg-green-600' },
  { value: 'skipped' as const,   label: '✗ Пропущен',  cls: 'bg-red-700 hover:bg-red-600' },
  { value: 'planned' as const,   label: '⏳ Запланирован', cls: 'bg-gray-600 hover:bg-gray-500' },
]

// ─── Day detail modal state ───────────────────────────────────────────────────
const showDayModal = ref(false)
const selectedDayRoute = ref<DailyRoute | null>(null)
const dayOptResult = ref<OptimizeVariantsResponse | null>(null)
const dayOptLoading = ref(false)
const dayOptError = ref<string | null>(null)
const selectedModel = ref<'qwen' | 'llama'>('qwen')
const selectedVariantId = ref<number | null>(null)
const confirmingVariant = ref(false)

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

// ─── Visit modal ──────────────────────────────────────────────────────────────
function openVisitModal(visit: VisitScheduleItem) {
  selectedVisit.value = visit
  visitForm.value = {
    status: visit.status,
    time_in: visit.time_in ?? '',
    time_out: visit.time_out ?? '',
    notes: '',
  }
  visitError.value = null
  showVisitModal.value = true
}

function closeVisitModal() {
  showVisitModal.value = false
  selectedVisit.value = null
}

async function submitVisitUpdate() {
  if (!selectedVisit.value) return
  savingVisit.value = true
  visitError.value = null
  try {
    const updated = await updateVisitStatus(selectedVisit.value.id, {
      status: visitForm.value.status,
      time_in: visitForm.value.time_in || undefined,
      time_out: visitForm.value.time_out || undefined,
      notes: visitForm.value.notes || undefined,
    })
    // Обновляем визит в локальном состоянии
    for (const route of routes.value) {
      const idx = route.visits.findIndex(v => v.id === updated.id)
      if (idx !== -1) {
        route.visits[idx] = updated
        break
      }
    }
    closeVisitModal()
  } catch (e: any) {
    visitError.value = e?.message ?? 'Ошибка сохранения'
  } finally {
    savingVisit.value = false
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function visitDuration(visit: VisitScheduleItem): number | null {
  if (!visit.time_in || !visit.time_out) return null
  const [h1, m1] = visit.time_in.split(':').map(Number)
  const [h2, m2] = visit.time_out.split(':').map(Number)
  const diff = (h2 * 60 + m2) - (h1 * 60 + m1)
  return diff > 0 ? diff : null
}

// ─── Экспорт в Excel ──────────────────────────────────────────────────────────
async function handleExport() {
  exportLoading.value = true
  try {
    await downloadScheduleExcel(currentMonth.value)
  } catch (e: any) {
    alert('Ошибка экспорта: ' + (e?.message ?? 'неизвестная ошибка'))
  } finally {
    exportLoading.value = false
  }
}

// ─── Day modal ────────────────────────────────────────────────────────────────
function openDayModal(route: DailyRoute) {
  selectedDayRoute.value = route
  dayOptResult.value = null
  dayOptError.value = null
  selectedVariantId.value = null
  showDayModal.value = true
}

async function optimizeDayRoute() {
  if (!selectedDayRoute.value) return
  dayOptLoading.value = true
  dayOptError.value = null
  dayOptResult.value = null
  selectedVariantId.value = null
  try {
    const locationIds = selectedDayRoute.value.visits.map(v => v.location_id)
    dayOptResult.value = await optimizeVariants(locationIds, selectedModel.value, {})
  } catch (e: any) {
    dayOptError.value = e?.message ?? 'Ошибка оптимизации'
  } finally {
    dayOptLoading.value = false
  }
}

async function confirmSelectedVariant() {
  if (!selectedDayRoute.value || !dayOptResult.value || selectedVariantId.value === null) return
  const variant = dayOptResult.value.variants.find(v => v.id === selectedVariantId.value)
  if (!variant) return
  confirmingVariant.value = true
  dayOptError.value = null
  try {
    const payload: ConfirmVariantRequest = {
      name: `${selectedDayRoute.value.rep_name} — ${selectedDayRoute.value.date} (${variant.name})`,
      locations: variant.locations,
      total_distance_km: variant.metrics.distance_km,
      total_time_hours: variant.metrics.time_hours,
      total_cost_rub: variant.metrics.cost_rub,
      quality_score: variant.metrics.quality_score,
      model_used: dayOptResult.value.model_used,
      original_location_ids: selectedDayRoute.value.visits.map(v => v.location_id),
    }
    await confirmVariant(payload)
    showDayModal.value = false
  } catch (e: any) {
    dayOptError.value = e?.message ?? 'Ошибка сохранения маршрута'
  } finally {
    confirmingVariant.value = false
  }
}


function statusLabel(s: string): string {
  return ({ completed: '✓', skipped: '✗', planned: '·', cancelled: '—', rescheduled: '↺' } as Record<string, string>)[s] ?? s
}

function statusColor(s: string): string {
  return ({ completed: 'text-green-400', skipped: 'text-red-400', cancelled: 'text-gray-500', rescheduled: 'text-yellow-400', planned: 'text-gray-400' } as Record<string, string>)[s] ?? 'text-gray-400'
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
function visitChipClass(visit: VisitScheduleItem) {
  if (visit.status === 'completed') return 'bg-green-700 text-white'
  if (visit.status === 'skipped') return 'bg-red-900 text-red-300 line-through'
  if (visit.status === 'cancelled') return 'bg-gray-700 text-gray-500 line-through'
  return `${catColor(visit.location_category ?? '?')} text-white`
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
.visit-chip { @apply text-xs px-2 py-0.5 rounded-full; }
.modal-overlay { @apply fixed inset-0 bg-black/60 flex items-center justify-center z-50; }
.modal { @apply bg-gray-800 border border-gray-600 rounded-lg p-6 w-full max-w-md; }
</style>
