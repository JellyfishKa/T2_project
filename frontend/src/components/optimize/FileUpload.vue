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
              Поддерживаемые форматы: CSV, JSON
            </p>
          </div>

          <div class="text-xs text-gray-500">Максимальный размер: 5MB</div>
        </div>

        <input
          ref="fileInput"
          type="file"
          accept=".csv,.json,.txt,text/csv,application/json"
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

      <!-- Uploaded Locations -->
      <div v-if="uploadedLocations.length > 0" class="mt-8">
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-sm font-medium text-gray-900">
            Загруженные магазины
          </h4>
          <span class="text-sm text-gray-500"
            >{{ uploadedLocations.length }} магазинов</span
          >
        </div>

        <div class="space-y-3">
          <div
            v-for="location in uploadedLocations"
            :key="location.id"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
          >
            <div class="flex items-center">
              <div
                class="flex-shrink-0 h-8 w-8 bg-green-100 rounded-lg flex items-center justify-center"
              >
                <svg
                  class="h-5 w-5 text-green-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm font-medium text-gray-900">
                  {{ location.name }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ location.city }}, {{ location.street }}, д.
                  {{ location.houseNumber }}
                </p>
              </div>
            </div>
            <button
              @click="addLocationToForm(location)"
              class="inline-flex items-center px-3 py-1 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Добавить в форму
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Location } from './types'

interface FilePreviewRow {
  [key: string]: string | number
}

interface UploadResponse {
  success: boolean
  message: string
  locations?: Location[]
  errors?: string[]
}

// Props & Emits
const emit = defineEmits<{
  'add-locations': [locations: Location[]]
}>()

// Refs
const fileInput = ref<HTMLInputElement>()
const dropZone = ref<HTMLElement>()
const isDragging = ref(false)
const isUploading = ref(false)
const selectedFile = ref<File | null>(null)
const previewData = ref<FilePreviewRow[]>([])
const allFileData = ref<FilePreviewRow[]>([]) // Храним все данные
const previewHeaders = ref<string[]>([])
const error = ref<string>('')
const successMessage = ref<string>('')
const validationErrors = ref<string[]>([])
const uploadedLocations = ref<Location[]>([])

// Computed
const canUpload = computed(() => {
  return allFileData.value.length > 0 && validationErrors.value.length === 0
})

// Methods
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

const processFile = (file: File) => {
  // Reset state
  resetState()
  selectedFile.value = file

  // Check file size (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
    error.value = 'Файл слишком большой. Максимальный размер: 5MB'
    return
  }

  // Check file type
  const fileExtension = file.name.split('.').pop()?.toLowerCase()
  const mimeType = file.type

  if (
    fileExtension === 'csv' ||
    mimeType === 'text/csv' ||
    mimeType === 'application/vnd.ms-excel'
  ) {
    parseCSV(file)
  } else if (fileExtension === 'json' || mimeType === 'application/json') {
    parseJSON(file)
  } else {
    error.value = 'Неподдерживаемый формат файла. Используйте CSV или JSON.'
  }
}

const parseCSV = (file: File) => {
  const reader = new FileReader()

  reader.onload = (event) => {
    try {
      const content = event.target?.result as string
      const lines = content.split('\n').filter((line) => line.trim())

      if (lines.length < 2) {
        error.value = 'Файл должен содержать хотя бы одну строку данных'
        return
      }

      // Parse headers
      const headers = lines[0].split(',').map((h) => h.trim())
      previewHeaders.value = headers

      // Parse ALL data rows
      const allDataRows: FilePreviewRow[] = []

      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map((v) => v.trim())
        const row: FilePreviewRow = {}

        headers.forEach((header, idx) => {
          row[header] = values[idx] || ''
        })

        allDataRows.push(row)
      }

      // Store all data
      allFileData.value = allDataRows

      // For preview, show first 5 rows
      previewData.value = allDataRows.slice(0, 5)

      // Validate all data, not just preview
      validateData(allDataRows)

      console.log(`Parsed ${allDataRows.length} rows from CSV`)
    } catch (err) {
      error.value = 'Ошибка при чтении CSV файла'
      console.error('CSV parsing error:', err)
    }
  }

  reader.onerror = () => {
    error.value = 'Ошибка при чтении файла'
  }

  reader.readAsText(file, 'UTF-8')
}

const parseJSON = (file: File) => {
  const reader = new FileReader()

  reader.onload = (event) => {
    try {
      const content = event.target?.result as string
      const data = JSON.parse(content)

      // Check if data is an array
      if (!Array.isArray(data)) {
        error.value = 'JSON должен содержать массив объектов'
        return
      }

      if (data.length === 0) {
        error.value = 'Файл не содержит данных'
        return
      }

      // Get headers from first object
      const firstItem = data[0]
      previewHeaders.value = Object.keys(firstItem)

      // Store ALL data
      allFileData.value = data

      // Get first 5 items for preview
      previewData.value = data.slice(0, 5).map((item) => {
        const row: FilePreviewRow = {}
        previewHeaders.value.forEach((header) => {
          row[header] = item[header] || ''
        })
        return row
      })

      // Validate all data, not just preview
      validateData(data)

      console.log(`Parsed ${data.length} rows from JSON`)
    } catch (err) {
      error.value = 'Ошибка при чтении JSON файла'
      console.error('JSON parsing error:', err)
    }
  }

  reader.onerror = () => {
    error.value = 'Ошибка при чтении файла'
  }

  reader.readAsText(file, 'UTF-8')
}

const validateData = (data: FilePreviewRow[]) => {
  validationErrors.value = []

  data.forEach((row, index) => {
    const rowNumber = index + 2 // +1 for header, +1 for 0-based index

    // Check required fields
    const requiredFields = [
      'name',
      'city',
      'street',
      'houseNumber',
      'latitude',
      'longitude'
    ]

    requiredFields.forEach((field) => {
      if (!row[field] || String(row[field]).trim() === '') {
        validationErrors.value.push(
          `Строка ${rowNumber}: Отсутствует обязательное поле "${field}"`
        )
      }
    })

    // Validate latitude
    if (row.latitude) {
      const lat = parseFloat(String(row.latitude))
      if (isNaN(lat) || lat < -90 || lat > 90) {
        validationErrors.value.push(
          `Строка ${rowNumber}: Некорректная широта "${row.latitude}"`
        )
      }
    }

    // Validate longitude
    if (row.longitude) {
      const lon = parseFloat(String(row.longitude))
      if (isNaN(lon) || lon < -180 || lon > 180) {
        validationErrors.value.push(
          `Строка ${rowNumber}: Некорректная долгота "${row.longitude}"`
        )
      }
    }

    // Validate house number
    if (row.houseNumber) {
      const houseNum = String(row.houseNumber).trim()
      if (!/^[1-9]\d*[а-яА-Я]?(\/\d+)?$/.test(houseNum)) {
        validationErrors.value.push(
          `Строка ${rowNumber}: Некорректный номер дома "${houseNum}"`
        )
      }
    }
  })
}

const uploadToServer = async () => {
  if (!selectedFile.value || !canUpload.value) return

  isUploading.value = true
  error.value = ''
  successMessage.value = ''

  try {
    // Create FormData
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    await new Promise((resolve) => setTimeout(resolve, 1500))

    const mockResponse: UploadResponse = {
      success: true,
      message: `Успешно загружено ${allFileData.value.length} магазинов`,
      locations: generateMockLocationsFromFile()
    }

    if (mockResponse.success && mockResponse.locations) {
      successMessage.value = mockResponse.message
      uploadedLocations.value = mockResponse.locations

      // Auto-add all locations to form starting from FIRST location
      emit('add-locations', mockResponse.locations)
    } else {
      error.value = mockResponse.message || 'Ошибка при загрузке'
    }
  } catch (err) {
    error.value = 'Ошибка сети при загрузке файла'
    console.error('Upload error:', err)
  } finally {
    isUploading.value = false
  }
}

const generateMockLocationsFromFile = (): Location[] => {
  return allFileData.value.map((row, index) => {
    // Function to capitalize first letter
    const capitalize = (str: string): string => {
      return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
    }

    return {
      id: `uploaded-${Date.now()}-${index}`,
      name: String(row.name || `Магазин ${index + 1}`),
      city: capitalize(String(row.city || 'Москва')),
      street: String(row.street || 'Тверская'),
      houseNumber: String(row.houseNumber || '1'),
      latitude: parseFloat(String(row.latitude || '55.7558')),
      longitude: parseFloat(String(row.longitude || '37.6173')),
      timeWindowStart: String(row.timeWindowStart || '09:00'),
      timeWindowEnd: String(row.timeWindowEnd || '18:00'),
      priority: String(row.priority || 'medium') as 'low' | 'medium' | 'high'
    }
  })
}

const addLocationToForm = (location: Location) => {
  emit('add-locations', [location])

  successMessage.value = `Магазин "${location.name}" добавлен в форму`
  setTimeout(() => {
    successMessage.value = ''
  }, 3000)
}

const clearUploadedData = () => {
  uploadedLocations.value = []
  successMessage.value = 'Загруженные данные очищены'
  setTimeout(() => {
    successMessage.value = ''
  }, 3000)
}

const resetState = () => {
  selectedFile.value = null
  previewData.value = []
  allFileData.value = []
  previewHeaders.value = []
  error.value = ''
  successMessage.value = ''
  validationErrors.value = []
}
</script>
