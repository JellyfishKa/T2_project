<template>
  <div class="space-y-6 py-6 md:py-8">
    <PageHero
      eyebrow="Команда"
      title="Торговые представители"
      description="Управляйте списком сотрудников, быстро меняйте статусы и не держите второстепенные поля перед глазами."
    >
      <template #actions>
        <button
          class="btn-primary"
          @click="showForm = true"
        >
          + Добавить сотрудника
        </button>
      </template>
    </PageHero>

    <div class="grid gap-4 md:grid-cols-3">
      <InfoStatCard label="Всего сотрудников" :value="reps.length" hint="Список активных и временно недоступных сотрудников." tone="blue" />
      <InfoStatCard label="Активны" :value="activeCount" hint="Готовы к маршрутам и планированию." tone="green" />
      <InfoStatCard label="Нуждают внимания" :value="inactiveCount" hint="Больничный, отпуск или недоступность." tone="amber" />
    </div>

    <!-- Форма добавления -->
    <div v-if="showForm" class="card p-5">
      <div class="flex items-start justify-between gap-3 mb-4">
        <div class="flex-1">
          <h2 class="font-semibold text-slate-950">Новый сотрудник</h2>
          <p class="mt-1 text-sm text-slate-500">Показываем только имя и статус, остальное лучше не перегружать на старте.</p>
        </div>
      </div>
      <div class="grid gap-3 md:grid-cols-[1fr_200px_220px_auto_auto] md:items-end">
        <div class="flex-1">
          <label class="label">ФИО</label>
          <input v-model="newName" class="input" placeholder="Иванов Иван Иванович" />
        </div>
        <div>
          <label class="label">Автомобиль</label>
          <select v-model="newVehicleId" class="input" data-testid="new-rep-vehicle-select">
            <option :value="null">Такси / Автобус</option>
            <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div>
          <label class="label">Статус</label>
          <select v-model="newStatus" class="input">
            <option value="active">Активен</option>
            <option value="sick">На больничном</option>
            <option value="vacation">В отпуске</option>
            <option value="unavailable">Недоступен</option>
          </select>
        </div>
        <button class="btn-primary" :disabled="saving" @click="createRep">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
        <button class="btn-secondary" @click="showForm = false">Отмена</button>
      </div>
    </div>

    <!-- Список -->
    <div v-if="loading" class="rounded-2xl border border-slate-200 bg-white p-6 text-slate-500 shadow-sm">Загрузка...</div>
    <div v-else-if="error" class="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-600 shadow-sm">{{ error }}</div>
    <div v-else class="grid gap-3">
      <div
        v-for="rep in reps"
        :key="rep.id"
        class="card p-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
      >
        <div>
          <div class="font-medium text-slate-950">{{ rep.name }}</div>
          <div class="mt-1 flex items-center gap-2 flex-wrap">
            <span class="text-sm text-slate-500">ID: {{ rep.id.slice(0, 8) }}…</span>
            <span v-if="rep.vehicle_name" class="badge badge-blue">🚗 {{ rep.vehicle_name }}</span>
            <span v-else class="badge badge-gray">🚕 Такси / Автобус</span>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <span :class="statusClass(rep.status)" class="badge">
            {{ statusLabel(rep.status) }}
          </span>
          <select
            :value="rep.status"
            class="input-sm"
            @change="updateStatus(rep.id, ($event.target as HTMLSelectElement).value)"
          >
            <option value="active">Активен</option>
            <option value="sick">На больничном</option>
            <option value="vacation">В отпуске</option>
            <option value="unavailable">Недоступен</option>
          </select>
          <select
            :value="rep.vehicle_id ?? ''"
            class="input-sm"
            @change="assignVehicle(rep.id, ($event.target as HTMLSelectElement).value || null)"
          >
            <option value="">Такси / Автобус</option>
            <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
          <button
            class="btn-danger-sm"
            @click="deleteRep(rep.id)"
          >
            Удалить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { SalesRep, Vehicle } from '@/services/types'
import {
  fetchReps,
  createRep as apiCreateRep,
  updateRep,
  deleteRep as apiDeleteRep,
  fetchVehicles,
  getApiErrorMessage,
} from '@/services/api'
import PageHero from '@/components/common/PageHero.vue'
import InfoStatCard from '@/components/common/InfoStatCard.vue'

const reps = ref<SalesRep[]>([])
const vehicles = ref<Vehicle[]>([])
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const showForm = ref(false)
const newName = ref('')
const newStatus = ref<SalesRep['status']>('active')
const newVehicleId = ref<string | null>(null)

const activeCount = computed(() =>
  reps.value.filter((rep) => rep.status === 'active').length
)

const inactiveCount = computed(() =>
  reps.value.filter((rep) => rep.status !== 'active').length
)

async function loadReps() {
  loading.value = true
  error.value = null
  try {
    const [repsResult, vehiclesResult] = await Promise.allSettled([
      fetchReps(),
      fetchVehicles(),
    ])

    if (repsResult.status === 'rejected') {
      error.value = getApiErrorMessage(repsResult.reason, 'Ошибка загрузки данных')
      reps.value = []
    } else {
      reps.value = repsResult.value
    }

    if (vehiclesResult.status === 'rejected') {
      vehicles.value = []
    } else {
      vehicles.value = vehiclesResult.value
    }
  } catch (e) {
    error.value = getApiErrorMessage(e, 'Ошибка загрузки данных')
  } finally {
    loading.value = false
  }
}

async function createRep() {
  if (!newName.value.trim() || saving.value) return
  saving.value = true
  error.value = null
  try {
    await apiCreateRep(newName.value.trim(), newStatus.value, newVehicleId.value)
    newName.value = ''
    newVehicleId.value = null
    showForm.value = false
    await loadReps()
  } catch (e) {
    error.value = getApiErrorMessage(e, 'Ошибка создания сотрудника')
  } finally {
    saving.value = false
  }
}

async function assignVehicle(id: string, vehicleId: string | null) {
  error.value = null
  try {
    const updated = await updateRep(id, { vehicle_id: vehicleId })
    const idx = reps.value.findIndex(r => r.id === id)
    if (idx !== -1) reps.value[idx] = updated
  } catch (e) {
    error.value = getApiErrorMessage(e, 'Ошибка привязки автомобиля')
  }
}

async function updateStatus(id: string, status: string) {
  error.value = null
  try {
    await updateRep(id, { status: status as SalesRep['status'] })
    await loadReps()
  } catch (e) {
    error.value = getApiErrorMessage(e, 'Ошибка обновления статуса')
  }
}

async function deleteRep(id: string) {
  if (!confirm('Удалить сотрудника?')) return
  error.value = null
  try {
    await apiDeleteRep(id)
    await loadReps()
  } catch (e: any) {
    error.value = getApiErrorMessage(e, 'Ошибка удаления сотрудника')
  }
}

function statusLabel(s: string) {
  return { active: 'Активен', sick: 'Больничный', vacation: 'Отпуск', unavailable: 'Недоступен' }[s] ?? s
}

function statusClass(s: string) {
  return {
    active: 'badge-green',
    sick: 'badge-red',
    vacation: 'badge-yellow',
    unavailable: 'badge-gray',
  }[s] ?? 'badge-gray'
}

onMounted(loadReps)
</script>

<style scoped>
.card { @apply bg-white rounded-lg border border-gray-200 shadow-sm; }
.input { @apply bg-white border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500; }
.input-sm { @apply bg-white border border-gray-300 rounded px-2 py-1 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500; }
.label { @apply block text-sm text-gray-600 mb-1; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded; }
.btn-secondary { @apply bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 text-sm px-4 py-2 rounded; }
.btn-danger-sm { @apply bg-red-600 hover:bg-red-700 text-white text-xs px-3 py-1 rounded; }
.badge { @apply text-xs px-2 py-0.5 rounded-full font-medium; }
.badge-green { @apply bg-green-100 text-green-800; }
.badge-red { @apply bg-red-100 text-red-800; }
.badge-yellow { @apply bg-yellow-100 text-yellow-800; }
.badge-gray { @apply bg-gray-100 text-gray-700; }
.badge-blue { @apply bg-blue-100 text-blue-800; }
</style>
