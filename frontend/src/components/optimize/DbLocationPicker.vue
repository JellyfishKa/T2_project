<template>
  <!-- Sidebar trigger card -->
  <div class="bg-white rounded-xl shadow-sm border border-gray-200">
    <div class="px-6 py-5 border-b border-gray-200">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">Торговые точки</h3>
          <p class="mt-1 text-sm text-gray-600">Выберите из базы или добавьте новую</p>
        </div>
        <button
          @click="openModal"
          class="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 3 8 3s8-.79 8-3V7M4 7c0 2.21 3.582 3 8 3s8-.79 8-3M4 7c0-2.21 3.582-3 8-3s8 .79 8 3" />
          </svg>
          Открыть базу
        </button>
      </div>
    </div>
    <div class="px-6 py-4">
      <p class="text-xs text-gray-400">
        Загружено из БД: <span class="font-medium text-gray-600">{{ cachedLocations.length }}</span> точек
        <template v-if="lastAdded > 0"> · Добавлено в форму: <span class="font-medium text-green-600">{{ lastAdded }}</span></template>
      </p>
    </div>
  </div>

  <!-- Modal -->
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="closeModal"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeModal" />

        <!-- Dialog -->
        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[88vh] flex flex-col z-10">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-5 border-b border-gray-200 flex-shrink-0">
            <h2 class="text-xl font-semibold text-gray-900">Торговые точки</h2>
            <button
              @click="closeModal"
              class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Tabs -->
          <div class="flex px-6 border-b border-gray-200 flex-shrink-0">
            <button
              @click="activeTab = 'db'"
              :class="[
                'py-3 px-4 text-sm font-medium border-b-2 -mb-px transition-colors',
                activeTab === 'db'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              ]"
            >
              Из базы данных
              <span v-if="cachedLocations.length" class="ml-1.5 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                {{ cachedLocations.length }}
              </span>
            </button>
            <button
              @click="activeTab = 'new'"
              :class="[
                'py-3 px-4 text-sm font-medium border-b-2 -mb-px transition-colors',
                activeTab === 'new'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              ]"
            >
              Новая точка
            </button>
          </div>

          <!-- ─── TAB: From DB ──────────────────────────────────────────────── -->
          <template v-if="activeTab === 'db'">
            <!-- Filters -->
            <div class="px-6 py-4 space-y-3 border-b border-gray-100 flex-shrink-0">
              <input
                v-model="search"
                type="text"
                placeholder="Поиск по названию или городу..."
                class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <div class="flex gap-2 flex-wrap">
                <button
                  v-for="cat in CATS"
                  :key="cat"
                  @click="filterCat = cat"
                  :class="[
                    'px-3 py-1 rounded-full text-xs font-medium border transition-colors',
                    filterCat === cat
                      ? catActiveClass(cat)
                      : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                  ]"
                >
                  {{ cat === 'all' ? 'Все' : cat }}
                </button>
              </div>
            </div>

            <!-- List -->
            <div class="flex-1 overflow-y-auto px-6 py-3">
              <div v-if="dbLoading" class="flex items-center justify-center py-16 text-sm text-gray-500">
                <svg class="animate-spin h-5 w-5 mr-2 text-blue-500" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Загрузка…
              </div>
              <div v-else-if="dbError" class="py-8 text-center text-sm text-red-600">
                {{ dbError }}
                <button @click="loadLocations" class="block mx-auto mt-2 text-blue-600 hover:underline">Повторить</button>
              </div>
              <div v-else-if="filtered.length === 0" class="py-8 text-center text-sm text-gray-400">
                {{ search || filterCat !== 'all' ? 'Ничего не найдено' : 'База пуста' }}
              </div>
              <template v-else>
                <!-- Select all row -->
                <div class="flex items-center justify-between mb-3">
                  <label class="flex items-center gap-2 text-xs text-gray-600 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      :checked="allFilteredSelected"
                      :indeterminate="someFilteredSelected && !allFilteredSelected"
                      @change="toggleAll"
                      class="rounded h-4 w-4 text-blue-600"
                    />
                    Выбрать все ({{ filtered.length }})
                  </label>
                  <span class="text-xs text-gray-500">Выбрано: {{ selected.size }}</span>
                </div>

                <div class="space-y-1">
                  <div
                    v-for="loc in filtered"
                    :key="loc.id"
                    @click="toggle(loc.id)"
                    :class="[
                      'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors select-none',
                      selected.has(loc.id)
                        ? 'bg-blue-50 border-blue-300'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                    ]"
                  >
                    <input
                      type="checkbox"
                      :checked="selected.has(loc.id)"
                      @click.stop="toggle(loc.id)"
                      class="h-4 w-4 text-blue-600 border-gray-300 rounded flex-shrink-0"
                    />
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-gray-900 truncate">{{ loc.name }}</p>
                      <p class="text-xs text-gray-500 truncate">
                        <template v-if="loc.city">{{ loc.city }} · </template>
                        {{ (loc.lat ?? 0).toFixed(4) }}, {{ (loc.lon ?? 0).toFixed(4) }}
                        <template v-if="loc.time_window_start"> · {{ loc.time_window_start }}–{{ loc.time_window_end }}</template>
                      </p>
                    </div>
                    <span
                      v-if="loc.category"
                      :class="['flex-shrink-0 text-xs px-2 py-0.5 rounded-full font-medium', catBadgeClass(loc.category)]"
                    >
                      {{ loc.category }}
                    </span>
                  </div>
                </div>
              </template>
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between flex-shrink-0">
              <button
                @click="loadLocations"
                :disabled="dbLoading"
                class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
              >
                <svg class="h-4 w-4" :class="dbLoading ? 'animate-spin' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Обновить
              </button>
              <button
                @click="addSelected"
                :disabled="selected.size === 0"
                class="inline-flex items-center gap-2 px-5 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Добавить {{ selected.size > 0 ? selected.size : '' }} в маршрут
              </button>
            </div>
          </template>

          <!-- ─── TAB: New Location ─────────────────────────────────────────── -->
          <template v-else>
            <div class="flex-1 overflow-y-auto px-6 py-5">
              <!-- Dedup warning -->
              <Transition name="fade">
                <div v-if="dedupWarning" class="mb-4 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
                  <span class="font-medium">Похожая точка уже есть в базе:</span> {{ dedupWarning }}
                </div>
              </Transition>

              <div class="space-y-4">
                <!-- Name -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
                  <input
                    v-model="newLoc.name"
                    @input="checkDedup"
                    type="text"
                    placeholder="Магазин «Магнит» на Советской"
                    :class="[
                      'w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                      newErrors.name ? 'border-red-300' : 'border-gray-300'
                    ]"
                  />
                  <p v-if="newErrors.name" class="mt-1 text-xs text-red-600">{{ newErrors.name }}</p>
                </div>

                <!-- Coordinates row -->
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Широта *</label>
                    <input
                      v-model.number="newLoc.lat"
                      type="number"
                      step="0.0001"
                      placeholder="54.1871"
                      :class="[
                        'w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                        newErrors.lat ? 'border-red-300' : 'border-gray-300'
                      ]"
                    />
                    <p v-if="newErrors.lat" class="mt-1 text-xs text-red-600">{{ newErrors.lat }}</p>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Долгота *</label>
                    <input
                      v-model.number="newLoc.lon"
                      type="number"
                      step="0.0001"
                      placeholder="45.1749"
                      :class="[
                        'w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                        newErrors.lon ? 'border-red-300' : 'border-gray-300'
                      ]"
                    />
                    <p v-if="newErrors.lon" class="mt-1 text-xs text-red-600">{{ newErrors.lon }}</p>
                  </div>
                </div>

                <!-- City + Category row -->
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Город</label>
                    <input
                      v-model="newLoc.city"
                      type="text"
                      placeholder="Саранск"
                      class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Категория</label>
                    <select
                      v-model="newLoc.category"
                      class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                    >
                      <option value="">— без категории —</option>
                      <option value="A">A (3 визита/мес, приоритет 1)</option>
                      <option value="B">B (2 визита/мес)</option>
                      <option value="C">C (1 визит/мес)</option>
                      <option value="D">D (1 визит/квартал)</option>
                    </select>
                  </div>
                </div>

                <!-- Time windows row -->
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Открытие</label>
                    <input
                      v-model="newLoc.time_window_start"
                      type="time"
                      class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Закрытие</label>
                    <input
                      v-model="newLoc.time_window_end"
                      type="time"
                      class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <!-- Address (optional) -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Адрес <span class="text-gray-400 font-normal">(необязательно)</span></label>
                  <input
                    v-model="newLoc.address"
                    type="text"
                    placeholder="ул. Советская, 23"
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <!-- Success message -->
                <Transition name="fade">
                  <div v-if="newSuccessMsg" class="rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-800">
                    {{ newSuccessMsg }}
                  </div>
                </Transition>

                <!-- Errors from server -->
                <Transition name="fade">
                  <div v-if="newError" class="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
                    {{ newError }}
                  </div>
                </Transition>

                <div class="flex gap-3 pt-1">
                  <button
                    @click="saveAndAdd"
                    :disabled="isSaving"
                    class="flex-1 inline-flex items-center justify-center gap-2 px-5 py-2.5 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <svg v-if="isSaving" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    {{ isSaving ? 'Сохранение…' : 'Сохранить в БД и добавить в маршрут' }}
                  </button>
                  <button
                    @click="resetNewForm"
                    type="button"
                    class="px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                  >
                    Сбросить
                  </button>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { fetchAllLocations, createLocation, getApiErrorMessage } from '@/services/api'
import { normalizeLocationCategory, resolveLocationPriority } from './locationPriority'
import type { Location } from './types'

const emit = defineEmits<{
  'add-locations': [locations: Location[]]
}>()

// ─── Modal state ─────────────────────────────────────────────────────────────
const isOpen = ref(false)
const activeTab = ref<'db' | 'new'>('db')
const lastAdded = ref(0)

// ─── DB tab state ─────────────────────────────────────────────────────────────
const dbLoading = ref(false)
const dbError = ref('')
const cachedLocations = ref<any[]>([])
const search = ref('')
const filterCat = ref<'all' | 'A' | 'B' | 'C' | 'D'>('all')
const selected = ref<Set<string>>(new Set())

const CATS = ['all', 'A', 'B', 'C', 'D'] as const

const filtered = computed(() => {
  let list = cachedLocations.value
  if (filterCat.value !== 'all') {
    list = list.filter(l => l.category === filterCat.value)
  }
  const q = search.value.trim().toLowerCase()
  if (q) {
    list = list.filter(l =>
      (l.name ?? '').toLowerCase().includes(q) ||
      (l.city ?? '').toLowerCase().includes(q)
    )
  }
  return list
})

const allFilteredSelected = computed(() =>
  filtered.value.length > 0 && filtered.value.every(l => selected.value.has(l.id))
)

const someFilteredSelected = computed(() =>
  filtered.value.some(l => selected.value.has(l.id))
)

function toggle(id: string) {
  const next = new Set(selected.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selected.value = next
}

function toggleAll() {
  if (allFilteredSelected.value) {
    const next = new Set(selected.value)
    filtered.value.forEach(l => next.delete(l.id))
    selected.value = next
  } else {
    const next = new Set(selected.value)
    filtered.value.forEach(l => next.add(l.id))
    selected.value = next
  }
}

async function loadLocations() {
  dbLoading.value = true
  dbError.value = ''
  try {
    const raw = await fetchAllLocations()
    cachedLocations.value = Array.isArray(raw) ? raw : []
  } catch (e: any) {
    dbError.value = getApiErrorMessage(e, 'Не удалось загрузить точки из базы')
  } finally {
    dbLoading.value = false
  }
}

function addSelected() {
  const toAdd = filtered.value.filter(l => selected.value.has(l.id))
  if (!toAdd.length) return

  const locations: Location[] = toAdd.map(loc => {
    const category = normalizeLocationCategory(loc.category)
    return {
      id: loc.id,
      name: loc.name ?? '',
      city: loc.city ?? '',
      street: loc.street ?? '',
      houseNumber: loc.house_number ?? '',
      address: loc.address ?? '',
      latitude: loc.lat ?? 0,
      longitude: loc.lon ?? 0,
      timeWindowStart: loc.time_window_start ?? '09:00',
      timeWindowEnd: loc.time_window_end ?? '18:00',
      priority: resolveLocationPriority({ priority: loc.priority, category }),
      category,
    }
  })

  emit('add-locations', locations)
  lastAdded.value += locations.length
  selected.value = new Set()
  closeModal()
}

// ─── New location tab state ───────────────────────────────────────────────────
const newLoc = ref({
  name: '',
  lat: null as number | null,
  lon: null as number | null,
  city: '',
  category: '',
  time_window_start: '09:00',
  time_window_end: '18:00',
  address: '',
})
const newErrors = ref({ name: '', lat: '', lon: '' })
const newError = ref('')
const newSuccessMsg = ref('')
const isSaving = ref(false)
const dedupWarning = ref('')

let dedupTimer: ReturnType<typeof setTimeout> | null = null
let successTimer: ReturnType<typeof setTimeout> | null = null

function checkDedup() {
  if (dedupTimer) clearTimeout(dedupTimer)
  dedupWarning.value = ''
  const name = newLoc.value.name.trim().toLowerCase()
  if (!name || name.length < 3) return
  dedupTimer = setTimeout(() => {
    const similar = cachedLocations.value.find(l =>
      (l.name ?? '').toLowerCase().includes(name) || name.includes((l.name ?? '').toLowerCase())
    )
    if (similar) dedupWarning.value = similar.name
  }, 400)
}

function validateNew(): boolean {
  newErrors.value = { name: '', lat: '', lon: '' }
  let ok = true
  if (!newLoc.value.name.trim()) {
    newErrors.value.name = 'Название обязательно'
    ok = false
  }
  if (newLoc.value.lat === null || isNaN(newLoc.value.lat) || newLoc.value.lat < -90 || newLoc.value.lat > 90) {
    newErrors.value.lat = 'Широта от -90 до 90'
    ok = false
  }
  if (newLoc.value.lon === null || isNaN(newLoc.value.lon) || newLoc.value.lon < -180 || newLoc.value.lon > 180) {
    newErrors.value.lon = 'Долгота от -180 до 180'
    ok = false
  }
  return ok
}

async function saveAndAdd() {
  if (!validateNew()) return
  isSaving.value = true
  newError.value = ''
  newSuccessMsg.value = ''

  try {
    const saved = await createLocation({
      name: newLoc.value.name.trim(),
      lat: newLoc.value.lat!,
      lon: newLoc.value.lon!,
      city: newLoc.value.city.trim() || undefined,
      category: newLoc.value.category || undefined,
      time_window_start: newLoc.value.time_window_start || undefined,
      time_window_end: newLoc.value.time_window_end || undefined,
      address: newLoc.value.address.trim() || undefined,
    })

    // Add to cache
    cachedLocations.value = [...cachedLocations.value, saved]

    // Emit to form
    const category = normalizeLocationCategory((saved as any).category)
    const loc: Location = {
      id: (saved as any).id,
      name: (saved as any).name ?? '',
      city: (saved as any).city ?? '',
      street: '',
      houseNumber: '',
      address: (saved as any).address ?? '',
      latitude: (saved as any).lat ?? 0,
      longitude: (saved as any).lon ?? 0,
      timeWindowStart: (saved as any).time_window_start ?? '09:00',
      timeWindowEnd: (saved as any).time_window_end ?? '18:00',
      priority: resolveLocationPriority({ category }),
      category,
    }
    emit('add-locations', [loc])
    lastAdded.value += 1

    newSuccessMsg.value = `«${(saved as any).name}» сохранена в БД и добавлена в маршрут`
    if (successTimer) clearTimeout(successTimer)
    successTimer = setTimeout(() => {
      newSuccessMsg.value = ''
      successTimer = null
    }, 4000)

    // Reset only name/coords, keep city/category for quick repeat entry
    newLoc.value.name = ''
    newLoc.value.lat = null
    newLoc.value.lon = null
    dedupWarning.value = ''
  } catch (e: any) {
    newError.value = getApiErrorMessage(e, 'Ошибка при сохранении точки')
  } finally {
    isSaving.value = false
  }
}

function resetNewForm() {
  newLoc.value = { name: '', lat: null, lon: null, city: '', category: '', time_window_start: '09:00', time_window_end: '18:00', address: '' }
  newErrors.value = { name: '', lat: '', lon: '' }
  newError.value = ''
  newSuccessMsg.value = ''
  dedupWarning.value = ''
}

// ─── Modal open/close ─────────────────────────────────────────────────────────
async function openModal() {
  isOpen.value = true
  if (cachedLocations.value.length === 0) {
    await loadLocations()
  }
}

function closeModal() {
  isOpen.value = false
}

// Escape key
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isOpen.value) closeModal()
}

import { onMounted, onUnmounted } from 'vue'
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  if (dedupTimer) clearTimeout(dedupTimer)
  if (successTimer) clearTimeout(successTimer)
})

// ─── Style helpers ────────────────────────────────────────────────────────────
function catBadgeClass(cat: string): string {
  if (cat === 'A') return 'bg-red-100 text-red-700'
  if (cat === 'B') return 'bg-yellow-100 text-yellow-700'
  if (cat === 'C') return 'bg-blue-100 text-blue-700'
  return 'bg-gray-100 text-gray-700'
}

function catActiveClass(cat: string): string {
  if (cat === 'A') return 'border-red-400 bg-red-50 text-red-700'
  if (cat === 'B') return 'border-yellow-400 bg-yellow-50 text-yellow-700'
  if (cat === 'C') return 'border-blue-400 bg-blue-50 text-blue-700'
  if (cat === 'D') return 'border-gray-400 bg-gray-100 text-gray-700'
  return 'border-blue-500 bg-blue-50 text-blue-700'
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
