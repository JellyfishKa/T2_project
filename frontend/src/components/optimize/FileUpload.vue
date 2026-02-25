<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200">
    <div class="px-6 py-5 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">
            Загрузка магазинов из файла
          </h3>
          <p class="mt-1 text-sm text-gray-600">
            Загрузите CSV или JSON файл со списком магазинов
          </p>
        </div>
        <button
          v-if="uploadedLocations.length > 0"
          @click="clearUploadedData"
          class="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          Очистить
        </button>
      </div>
    </div>

    <div class="px-6 py-5">
      <!-- Drag & Drop Area -->
      <div
        ref="dropZone"
        @click="triggerFileInput"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        :class="[
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200',
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
        ]"
      >
        <div class="space-y-4">
          <div class="mx-auto w-12 h-12">
            <svg
              class="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          <div class="space-y-2">
            <p class="text-sm font-medium text-gray-900">
              <span class="text-blue-600">Нажмите для выбора файла</span> или
              перетащите его сюда
            </p>
            <p class="text-sm text-gray-500">
              Поддерживаемые форматы: CSV, JSON, XLSX
            </p>
            <p class="text-xs text-gray-400">
              Колонки: name, lat, lon (и опционально time_window_start, time_window_end)
            </p>
          </div>

          <div class="text-xs text-gray-500">Максимальный размер: 5MB</div>
        </div>

        <input
          ref="fileInput"
          type="file"
          accept=".csv,.json,.xlsx,.xls,text/csv,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          @change="handleFileSelect"
          class="hidden"
        />
      </div>

      <!-- Error Message -->
      <div v-if="error" class="mt-4">
        <div class="rounded-md bg-red-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg
                class="h-5 w-5 text-red-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">Ошибка загрузки</h3>
              <div class="mt-2 text-sm text-red-700">
                <p>{{ error }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="mt-4">
        <div class="rounded-md bg-green-50 p-4">
          <div class="flex">
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
              <h3 class="text-sm font-medium text-green-800">Успешно!</h3>
              <div class="mt-2 text-sm text-green-700">
                <p>{{ successMessage }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Preview Table -->
      <div v-if="previewData.length > 0" class="mt-6">
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-sm font-medium text-gray-900">
            Предпросмотр данных (первые 5 строк)
          </h4>
          <span class="text-sm text-gray-500"
            >{{ previewData.length }} строк</span
          >
        </div>

        <div class="overflow-x-auto border border-gray-200 rounded-lg">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th
                  v-for="header in previewHeaders"
                  :key="header"
                  scope="col"
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {{ header }}
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(row, index) in previewData" :key="index">
                <td
                  v-for="header in previewHeaders"
                  :key="`${index}-${header}`"
                  class="px-4 py-3 text-sm text-gray-900 whitespace-nowrap"
                >
                  {{ row[header] || '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mt-4 text-sm text-gray-500">
          Обнаружено {{ previewData.length }} магазинов.
          {{
            validationErrors.length > 0
              ? `Найдено ${validationErrors.length} ошибок.`
              : 'Все данные корректны.'
          }}
        </div>

        <!-- Validation Errors -->
        <div v-if="validationErrors.length > 0" class="mt-4">
          <div class="rounded-md bg-yellow-50 p-4">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg
                  class="h-5 w-5 text-yellow-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
              <div class="ml-3">
                <h3 class="text-sm font-medium text-yellow-800">
                  Обнаружены ошибки в данных
                </h3>
                <div class="mt-2 text-sm text-yellow-700">
                  <ul class="list-disc pl-5 space-y-1">
                    <li
                      v-for="(error, idx) in validationErrors.slice(0, 5)"
                      :key="idx"
                    >
                      {{ error }}
                    </li>
                    <li v-if="validationErrors.length > 5">
                      ... и еще {{ validationErrors.length - 5 }} ошибок
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Upload Button -->
        <div class="mt-6 flex justify-end">
          <button
            type="button"
            @click="uploadToServer"
            :disabled="isUploading || validationErrors.length > 0"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              v-if="isUploading"
              class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            {{ isUploading ? 'Загрузка...' : 'Загрузить на сервер' }}
          </button>
        </div>
      </div>

      <!-- Uploaded Locations — выбор и добавление в форму -->
      <div v-if="uploadedLocations.length > 0" class="mt-8">
        <!-- Заголовок + кнопки действий -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div class="flex items-center gap-3">
            <h4 class="text-sm font-medium text-gray-900">
              Загруженные магазины
            </h4>
            <span class="text-sm text-gray-500">
              {{ uploadedLocations.length }} шт., выбрано: {{ selectedIds.size }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="toggleSelectAll"
              class="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              {{ selectedIds.size === uploadedLocations.length ? 'Снять все' : 'Выбрать все' }}
            </button>
            <button
              @click="addSelectedToForm"
              :disabled="selectedIds.size === 0"
              class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Добавить выделенные ({{ selectedIds.size }})
            </button>
            <button
              @click="addAllToForm"
              class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
            >
              Добавить все ({{ uploadedLocations.length }})
            </button>
          </div>
        </div>

        <!-- Список с чекбоксами -->
        <div class="space-y-2 max-h-80 overflow-y-auto pr-1">
          <div
            v-for="location in uploadedLocations"
            :key="location.id"
            @click="toggleSelect(location.id)"
            :class="[
              'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors',
              selectedIds.has(location.id)
                ? 'bg-blue-50 border-blue-300'
                : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
            ]"
          >
            <!-- Чекбокс -->
            <input
              type="checkbox"
              :checked="selectedIds.has(location.id)"
              @click.stop="toggleSelect(location.id)"
              class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <!-- Иконка -->
            <div class="flex-shrink-0 h-8 w-8 bg-green-100 rounded-lg flex items-center justify-center">
              <svg class="h-4 w-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <!-- Данные -->
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-gray-900 truncate">
                {{ location.name }}
              </p>
              <p class="text-xs text-gray-500">
                {{ location.city }}
                <template v-if="location.street"> · {{ location.street }}<template v-if="location.houseNumber">, {{ location.houseNumber }}</template></template>
                &nbsp;·&nbsp;{{ location.latitude.toFixed(4) }}, {{ location.longitude.toFixed(4) }}
                &nbsp;·&nbsp;{{ location.timeWindowStart }}–{{ location.timeWindowEnd }}
              </p>
            </div>
            <!-- Приоритет -->
            <span
              :class="[
                'flex-shrink-0 text-xs px-2 py-0.5 rounded-full font-medium',
                location.priority === 'high' ? 'bg-red-100 text-red-700' :
                location.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                'bg-gray-100 text-gray-600'
              ]"
            >
              {{ location.priority === 'high' ? 'Высокий' : location.priority === 'medium' ? 'Средний' : 'Низкий' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { uploadLocations } from '@/services/api'
import type { Location } from './types'

interface FilePreviewRow {
  [key: string]: string | number
}

// Props & Emits
const emit = defineEmits<{
  'add-locations': [locations: Location[]]
}>()

// Refs
const fileInput = ref<HTMLInputElement>()
const isDragging = ref(false)
const isUploading = ref(false)
const selectedFile = ref<File | null>(null)
const previewData = ref<FilePreviewRow[]>([])
const allFileData = ref<FilePreviewRow[]>([])
const previewHeaders = ref<string[]>([])
const error = ref<string>('')
const successMessage = ref<string>('')
const validationErrors = ref<string[]>([])
const uploadedLocations = ref<Location[]>([])
// Множество выбранных id для чекбоксов
const selectedIds = ref<Set<string>>(new Set())

// Computed
const canUpload = computed(
  () => allFileData.value.length > 0 && validationErrors.value.length === 0
)

// Methods
const triggerFileInput = () => fileInput.value?.click()

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files && files.length > 0) processFile(files[0])
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0) processFile(files[0])
}

const processFile = (file: File) => {
  resetState()
  selectedFile.value = file

  if (file.size > 5 * 1024 * 1024) {
    error.value = 'Файл слишком большой. Максимальный размер: 5MB'
    return
  }

  const ext = file.name.split('.').pop()?.toLowerCase()

  if (ext === 'csv') {
    parseCSV(file)
  } else if (ext === 'json') {
    parseJSON(file)
  } else if (ext === 'xlsx' || ext === 'xls') {
    // XLSX — предпросмотр недоступен в браузере без библиотеки,
    // сразу выставляем файл как готовый к загрузке
    previewHeaders.value = ['name', 'lat', 'lon', 'time_window_start', 'time_window_end']
    allFileData.value = [{ name: '(данные из XLSX)', lat: 0, lon: 0, time_window_start: '', time_window_end: '' }]
    previewData.value = allFileData.value
    successMessage.value = `Файл ${file.name} готов к загрузке. Нажмите "Загрузить на сервер".`
  } else {
    error.value = 'Неподдерживаемый формат. Используйте CSV, JSON или XLSX.'
  }
}

const parseCSV = (file: File) => {
  const reader = new FileReader()
  reader.onload = (event) => {
    try {
      const content = event.target?.result as string
      const lines = content.split('\n').filter((l) => l.trim())
      if (lines.length < 2) {
        error.value = 'Файл должен содержать хотя бы одну строку данных'
        return
      }
      const headers = lines[0].split(',').map((h) => h.trim())
      previewHeaders.value = headers
      const rows: FilePreviewRow[] = []
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map((v) => v.trim())
        const row: FilePreviewRow = {}
        headers.forEach((h, idx) => { row[h] = values[idx] || '' })
        rows.push(row)
      }
      allFileData.value = rows
      previewData.value = rows.slice(0, 5)
      validateData(rows)
    } catch {
      error.value = 'Ошибка при чтении CSV файла'
    }
  }
  reader.onerror = () => { error.value = 'Ошибка при чтении файла' }
  reader.readAsText(file, 'UTF-8')
}

const parseJSON = (file: File) => {
  const reader = new FileReader()
  reader.onload = (event) => {
    try {
      const data = JSON.parse(event.target?.result as string)
      if (!Array.isArray(data) || data.length === 0) {
        error.value = 'JSON должен содержать непустой массив объектов'
        return
      }
      previewHeaders.value = Object.keys(data[0])
      allFileData.value = data
      previewData.value = data.slice(0, 5)
      validateData(data)
    } catch {
      error.value = 'Ошибка при чтении JSON файла'
    }
  }
  reader.onerror = () => { error.value = 'Ошибка при чтении файла' }
  reader.readAsText(file, 'UTF-8')
}

/**
 * Валидация: обязательные поля name + координаты (lat/lon или latitude/longitude).
 * Поля city/street/houseNumber — необязательны, файл их не содержит.
 */
const validateData = (data: FilePreviewRow[]) => {
  validationErrors.value = []
  data.forEach((row, idx) => {
    const rowNum = idx + 2
    if (!row['name'] && !row['название'] && !row['наименование точки']) {
      validationErrors.value.push(`Строка ${rowNum}: отсутствует поле "name"`)
    }
    const lat = row['lat'] ?? row['latitude'] ?? row['широта']
    const lon = row['lon'] ?? row['longitude'] ?? row['долгота']
    if (lat !== undefined && lat !== '') {
      const v = parseFloat(String(lat))
      if (isNaN(v) || v < -90 || v > 90)
        validationErrors.value.push(`Строка ${rowNum}: некорректная широта "${lat}"`)
    }
    if (lon !== undefined && lon !== '') {
      const v = parseFloat(String(lon))
      if (isNaN(v) || v < -180 || v > 180)
        validationErrors.value.push(`Строка ${rowNum}: некорректная долгота "${lon}"`)
    }
  })
}

/**
 * Загружает файл на сервер через реальный API POST /api/v1/locations/upload.
 * Бэкенд сам парсит CSV/JSON/XLSX и возвращает {created: [...], errors: [...]}.
 */
const uploadToServer = async () => {
  if (!selectedFile.value || !canUpload.value) return

  isUploading.value = true
  error.value = ''
  successMessage.value = ''

  try {
    const result = await uploadLocations(selectedFile.value)

    // Бэкенд возвращает {created: Location[], errors: [], total_processed: N}
    const created = (result as any).created ?? result.locations ?? []
    const errors = (result as any).errors ?? []

    if (created.length > 0) {
      successMessage.value = `Загружено ${created.length} магазинов.`
      if (errors.length > 0)
        successMessage.value += ` Пропущено строк с ошибками: ${errors.length}.`

      // Конвертируем формат бэкенда → формат фронтенда.
      // city: берём из данных файла если есть, иначе извлекаем из name.
      const locations: Location[] = created.map((loc: any, i: number) => {
        const cityFromData = loc.city ?? ''
        // Пытаемся определить город из названия (последнее слово или известный список)
        const cityGuess = cityFromData || guessCityFromName(loc.name ?? '')
        const streetFromData = loc.street ?? ''
        const houseFromData = loc.houseNumber ?? loc.house_number ?? ''

        return {
          id: loc.id ?? `srv-${Date.now()}-${i}`,
          name: loc.name ?? '',
          city: cityGuess || 'Саранск',
          street: streetFromData,
          houseNumber: houseFromData,
          latitude: loc.lat ?? loc.latitude ?? 0,
          longitude: loc.lon ?? loc.longitude ?? 0,
          timeWindowStart: loc.time_window_start ?? '09:00',
          timeWindowEnd: loc.time_window_end ?? '18:00',
          priority: (loc.priority === 'high' || loc.priority === 'low'
            ? loc.priority
            : 'medium') as 'low' | 'medium' | 'high'
        }
      })

      uploadedLocations.value = locations
      selectedIds.value = new Set()
      // НЕ эмитим автоматически — пусть пользователь сам выберет
    } else {
      error.value = 'Сервер не вернул ни одной локации. Проверьте формат файла.'
      if (errors.length > 0) {
        error.value += ` Ошибки: ${errors.slice(0, 3).map((e: any) => e.error ?? JSON.stringify(e)).join('; ')}`
      }
    }
  } catch (err: any) {
    error.value = err?.message ?? err?.detail ?? 'Ошибка при загрузке файла на сервер'
    console.error('Upload error:', err)
  } finally {
    isUploading.value = false
  }
}

// ─── Выбор чекбоксами ───────────────────────────────────────────────────────
const toggleSelect = (id: string) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedIds.value = next
}

const toggleSelectAll = () => {
  if (selectedIds.value.size === uploadedLocations.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(uploadedLocations.value.map((l) => l.id))
  }
}

const addSelectedToForm = () => {
  const toAdd = uploadedLocations.value.filter((l) => selectedIds.value.has(l.id))
  if (toAdd.length === 0) return
  emit('add-locations', toAdd)
  successMessage.value = `Добавлено ${toAdd.length} магазин(ов) в форму`
  setTimeout(() => { successMessage.value = '' }, 3000)
}

const addAllToForm = () => {
  emit('add-locations', uploadedLocations.value)
  successMessage.value = `Все ${uploadedLocations.value.length} магазинов добавлены в форму`
  setTimeout(() => { successMessage.value = '' }, 3000)
}

const clearUploadedData = () => {
  uploadedLocations.value = []
  selectedIds.value = new Set()
  successMessage.value = 'Загруженные данные очищены'
  setTimeout(() => { successMessage.value = '' }, 3000)
}

const resetState = () => {
  selectedFile.value = null
  previewData.value = []
  allFileData.value = []
  previewHeaders.value = []
  error.value = ''
  successMessage.value = ''
  validationErrors.value = []
  uploadedLocations.value = []
  selectedIds.value = new Set()
}

// ─── Вспомогательная: угадать город из названия магазина ─────────────────────
const KNOWN_CITIES: Record<string, string> = {
  'саранск': 'Саранск',
  'рузаевка': 'Рузаевка',
  'ковылкино': 'Ковылкино',
  'краснослободск': 'Краснослободск',
  'темников': 'Темников',
  'ардатов': 'Ардатов',
  'чамзинка': 'Чамзинка',
  'инсар': 'Инсар',
  'торбеево': 'Торбеево',
  'зубова поляна': 'Зубова Поляна',
  'ельники': 'Ельники',
  'атяшево': 'Атяшево',
  'лямбирь': 'Лямбирь',
  'комсомольский': 'Комсомольский',
}

const guessCityFromName = (name: string): string => {
  const lower = name.toLowerCase()
  for (const [key, city] of Object.entries(KNOWN_CITIES)) {
    if (lower.includes(key)) return city
  }
  return ''
}
</script>
