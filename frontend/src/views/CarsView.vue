<template>
  <div class="p-6 max-w-5xl mx-auto space-y-6">
    <PageHero title="Автопарк" subtitle="Управление автомобилями и транспортными тарифами" />

    <!-- Error -->
    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded">
      {{ error }}
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <InfoStatCard label="Всего автомобилей" :value="String(vehicles.length)" />
      <InfoStatCard label="Ср. расход (город)" :value="avgCityConsumption" />
      <InfoStatCard label="Ср. расход (трасса)" :value="avgHighwayConsumption" />
      <InfoStatCard label="Ср. цена топлива" :value="avgFuelPrice" />
    </div>

    <!-- Add form -->
    <div class="card p-5">
      <h2 class="font-semibold text-gray-800 mb-4">Добавить автомобиль</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div>
          <label class="label">Название</label>
          <input v-model="form.name" class="input" placeholder="Lada Granta" />
        </div>
        <div>
          <label class="label">Цена топлива (₽/л)</label>
          <input v-model.number="form.fuel_price_rub" type="number" min="0" step="0.5" class="input" placeholder="63" />
        </div>
        <div>
          <label class="label">Расход город (л/100км)</label>
          <input v-model.number="form.consumption_city_l_100km" type="number" min="0" step="0.1" class="input" placeholder="9.0" />
        </div>
        <div>
          <label class="label">Расход трасса (л/100км)</label>
          <input v-model.number="form.consumption_highway_l_100km" type="number" min="0" step="0.1" class="input" placeholder="6.5" />
        </div>
      </div>
      <div class="flex gap-2 mt-4">
        <button class="btn-primary" :disabled="!isFormValid || saving" @click="addVehicle">
          {{ saving ? 'Сохранение...' : 'Добавить' }}
        </button>
        <label class="btn-secondary cursor-pointer">
          Загрузить JSON
          <input type="file" accept=".json" class="hidden" @change="handleUpload" />
        </label>
      </div>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500 text-sm">Загрузка...</div>
      <div v-else-if="vehicles.length === 0" class="p-8 text-center text-gray-500 text-sm">
        Нет автомобилей — добавьте вручную или загрузите JSON
      </div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Название</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">₽/л</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">л/100км город</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">л/100км трасса</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">₽/100км город</th>
            <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Действия</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="v in vehicles" :key="v.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-medium text-gray-900">{{ v.name }}</td>
            <td class="px-4 py-3 text-right text-gray-700">{{ v.fuel_price_rub.toFixed(1) }}</td>
            <td class="px-4 py-3 text-right text-gray-700">{{ v.consumption_city_l_100km.toFixed(1) }}</td>
            <td class="px-4 py-3 text-right text-gray-700">{{ v.consumption_highway_l_100km.toFixed(1) }}</td>
            <td class="px-4 py-3 text-right text-gray-700">
              {{ ((v.consumption_city_l_100km / 100) * v.fuel_price_rub * 100).toFixed(0) }}
            </td>
            <td class="px-4 py-3 text-center">
              <button class="btn-danger-sm" @click="removeVehicle(v.id)">Удалить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Transport mode rates reference -->
    <div class="card p-5">
      <h2 class="font-semibold text-gray-800 mb-3">Тарифы без авто</h2>
      <p class="text-xs text-gray-500 mb-3">
        Используются при выборе режима «Такси» или «Автобус» в маршрутах.
      </p>
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div class="text-sm font-semibold text-yellow-800 mb-1">🚕 Такси</div>
          <div class="text-2xl font-bold text-yellow-900">20 ₽/км</div>
          <div class="text-xs text-yellow-700 mt-1">километровый тариф</div>
        </div>
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div class="text-sm font-semibold text-blue-800 mb-1">🚌 Автобус</div>
          <div class="text-2xl font-bold text-blue-900">33 ₽/пересадка</div>
          <div class="text-xs text-blue-700 mt-1">плоский тариф за каждый перегон</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Vehicle } from '@/services/types'
import { fetchVehicles, createVehicle, deleteVehicle } from '@/services/api'
import PageHero from '@/components/common/PageHero.vue'
import InfoStatCard from '@/components/common/InfoStatCard.vue'

const vehicles = ref<Vehicle[]>([])
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const form = ref({
  name: '',
  fuel_price_rub: null as number | null,
  consumption_city_l_100km: null as number | null,
  consumption_highway_l_100km: null as number | null,
})

const isFormValid = computed(() =>
  form.value.name.trim() &&
  form.value.fuel_price_rub !== null && form.value.fuel_price_rub > 0 &&
  form.value.consumption_city_l_100km !== null && form.value.consumption_city_l_100km > 0 &&
  form.value.consumption_highway_l_100km !== null && form.value.consumption_highway_l_100km > 0
)

const avgCityConsumption = computed(() => {
  if (!vehicles.value.length) return '—'
  const avg = vehicles.value.reduce((s, v) => s + v.consumption_city_l_100km, 0) / vehicles.value.length
  return `${avg.toFixed(1)} л/100км`
})

const avgHighwayConsumption = computed(() => {
  if (!vehicles.value.length) return '—'
  const avg = vehicles.value.reduce((s, v) => s + v.consumption_highway_l_100km, 0) / vehicles.value.length
  return `${avg.toFixed(1)} л/100км`
})

const avgFuelPrice = computed(() => {
  if (!vehicles.value.length) return '—'
  const avg = vehicles.value.reduce((s, v) => s + v.fuel_price_rub, 0) / vehicles.value.length
  return `${avg.toFixed(1)} ₽/л`
})

async function loadVehicles() {
  loading.value = true
  error.value = null
  try {
    vehicles.value = await fetchVehicles()
  } catch {
    error.value = 'Ошибка загрузки автомобилей'
  } finally {
    loading.value = false
  }
}

async function addVehicle() {
  if (!isFormValid.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    const v = await createVehicle({
      name: form.value.name.trim(),
      fuel_price_rub: form.value.fuel_price_rub!,
      consumption_city_l_100km: form.value.consumption_city_l_100km!,
      consumption_highway_l_100km: form.value.consumption_highway_l_100km!,
    })
    vehicles.value.push(v)
    form.value = { name: '', fuel_price_rub: null, consumption_city_l_100km: null, consumption_highway_l_100km: null }
  } catch {
    error.value = 'Ошибка добавления автомобиля'
  } finally {
    saving.value = false
  }
}

async function removeVehicle(id: string) {
  if (!confirm('Удалить автомобиль? Сотрудники, у которых он назначен, потеряют привязку.')) return
  error.value = null
  try {
    await deleteVehicle(id)
    vehicles.value = vehicles.value.filter(v => v.id !== id)
  } catch {
    error.value = 'Ошибка удаления автомобиля'
  }
}

async function handleUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  error.value = null
  try {
    const { default: axios } = await import('axios')
    const formData = new FormData()
    formData.append('file', file)
    const base = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
    const response = await axios.post(`${base}/routing/upload_cars`, formData)
    vehicles.value.push(...response.data)
  } catch (e: any) {
    error.value = `Ошибка загрузки: ${e?.response?.data?.detail ?? e?.message ?? e}`
  } finally {
    target.value = ''
  }
}

onMounted(loadVehicles)
</script>

<style scoped>
.card { @apply bg-white rounded-lg border border-gray-200 shadow-sm; }
.input { @apply bg-white border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500; }
.label { @apply block text-sm text-gray-600 mb-1; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded; }
.btn-secondary { @apply bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 text-sm px-4 py-2 rounded; }
.btn-danger-sm { @apply bg-red-600 hover:bg-red-700 text-white text-xs px-3 py-1 rounded; }
</style>
