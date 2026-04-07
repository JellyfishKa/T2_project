<template>
  <div class="reps-view p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Торговые представители</h1>
      <button
        class="btn-primary"
        @click="showForm = true"
      >
        + Добавить сотрудника
      </button>
    </div>

    <!-- Форма добавления -->
    <div v-if="showForm" class="card mb-6 p-4">
      <h2 class="font-semibold mb-3">Новый сотрудник</h2>
      <div class="flex gap-3 items-end">
        <div class="flex-1">
          <label class="label">ФИО</label>
          <input v-model="newName" class="input" placeholder="Иванов Иван Иванович" />
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
        <button class="btn-primary" @click="createRep">Сохранить</button>
        <button class="btn-secondary" @click="showForm = false">Отмена</button>
      </div>
    </div>

    <!-- Список -->
    <div v-if="loading" class="text-gray-500">Загрузка...</div>
    <div v-else-if="error" class="text-red-500">{{ error }}</div>
    <div v-else class="grid gap-3">
      <div
        v-for="rep in reps"
        :key="rep.id"
        class="card p-4 flex items-center justify-between"
      >
        <div>
          <div class="font-medium text-gray-900">{{ rep.name }}</div>
          <div class="text-sm text-gray-500">ID: {{ rep.id.slice(0, 8) }}…</div>
        </div>
        <div class="flex items-center gap-3">
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
import { ref, onMounted } from 'vue'
import type { SalesRep } from '@/services/types'
import {
  fetchReps,
  createRep as apiCreateRep,
  updateRep,
  deleteRep as apiDeleteRep,
} from '@/services/api'

const reps = ref<SalesRep[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showForm = ref(false)
const newName = ref('')
const newStatus = ref<SalesRep['status']>('active')

async function loadReps() {
  loading.value = true
  error.value = null
  try {
    reps.value = await fetchReps()
  } catch (e) {
    error.value = 'Ошибка загрузки сотрудников'
  } finally {
    loading.value = false
  }
}

async function createRep() {
  if (!newName.value.trim()) return
  await apiCreateRep(newName.value.trim(), newStatus.value)
  newName.value = ''
  showForm.value = false
  await loadReps()
}

async function updateStatus(id: string, status: string) {
  await updateRep(id, { status: status as SalesRep['status'] })
  await loadReps()
}

async function deleteRep(id: string) {
  if (!confirm('Удалить сотрудника?')) return
  await apiDeleteRep(id)
  await loadReps()
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
</style>
