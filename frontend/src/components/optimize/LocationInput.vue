<template>
  <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center">
        <div
          class="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-lg flex items-center justify-center"
        >
          <span class="text-blue-600 font-bold">{{ index + 1 }}</span>
        </div>
        <div class="ml-3">
          <h4 class="text-sm font-medium text-gray-900">
            Магазин {{ index + 1 }}
          </h4>
          <p v-if="location.name" class="text-sm text-gray-500">
            {{ location.name }}
          </p>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <button
          type="button"
          @click="$emit('remove', index)"
          class="text-gray-400 hover:text-red-500 transition-colors"
          :disabled="isFirstLocation"
          :class="{ 'opacity-50 cursor-not-allowed': isFirstLocation }"
        >
          <svg
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Store Name -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Название магазина *
        </label>
        <input
          type="text"
          v-model="localLocation.name"
          @input="updateLocation"
          :class="[
            'block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            !localLocation.name.trim() || nameError
              ? 'border-red-300'
              : 'border-gray-300'
          ]"
          placeholder="ТЦ Авиапарк, Магазин №1"
        />
        <p v-if="nameError" class="mt-1 text-xs text-red-600">
          {{ nameError }}
        </p>
      </div>

      <!-- City -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Город *
        </label>
        <input
          type="text"
          v-model="localLocation.city"
          @input="updateLocation"
          :class="[
            'block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            !localLocation.city.trim() || cityError
              ? 'border-red-300'
              : 'border-gray-300'
          ]"
          placeholder="Москва"
        />
        <p v-if="cityError" class="mt-1 text-xs text-red-600">
          {{ cityError }}
        </p>
      </div>

      <!-- Street (опционально) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Улица
          <span class="text-gray-400 font-normal text-xs ml-1">(необязательно)</span>
        </label>
        <input
          type="text"
          v-model="localLocation.street"
          @input="updateLocation"
          :class="[
            'block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            streetError ? 'border-red-300' : 'border-gray-300'
          ]"
          placeholder="ул. Советская, пр. Ленина"
        />
        <p v-if="streetError" class="mt-1 text-xs text-red-600">
          {{ streetError }}
        </p>
      </div>

      <!-- House Number (опционально) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Номер дома
          <span class="text-gray-400 font-normal text-xs ml-1">(необязательно)</span>
        </label>
        <input
          type="text"
          v-model="localLocation.houseNumber"
          @input="updateLocation"
          :class="[
            'block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            houseNumberError ? 'border-red-300' : 'border-gray-300'
          ]"
          placeholder="35"
        />
        <p v-if="houseNumberError" class="mt-1 text-xs text-red-600">
          {{ houseNumberError }}
        </p>
        <p class="mt-1 text-xs text-gray-500">Примеры: 16, 101А, 11/4</p>
      </div>

      <!-- Coordinates -->
      <div class="md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Широта
          </label>
          <div class="flex items-center">
            <input
              type="number"
              step="0.000001"
              v-model.number="localLocation.latitude"
              @input="updateLocation"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="55.7558"
            />
            <span class="ml-2 text-sm text-gray-500">°N</span>
          </div>
          <p v-if="latitudeError" class="mt-1 text-xs text-red-600">
            {{ latitudeError }}
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Долгота
          </label>
          <div class="flex items-center">
            <input
              type="number"
              step="0.000001"
              v-model.number="localLocation.longitude"
              @input="updateLocation"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="37.6173"
            />
            <span class="ml-2 text-sm text-gray-500">°E</span>
          </div>
          <p v-if="longitudeError" class="mt-1 text-xs text-red-600">
            {{ longitudeError }}
          </p>
        </div>
      </div>

      <!-- Time Windows -->
      <div class="md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Начало временного окна *
          </label>
          <input
            type="time"
            v-model="localLocation.timeWindowStart"
            @input="updateLocation"
            :class="[
              'block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
              !localLocation.timeWindowStart
                ? 'border-red-300'
                : 'border-gray-300'
            ]"
          />
          <p v-if="timeWindowStartError" class="mt-1 text-xs text-red-600">
            {{ timeWindowStartError }}
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Конец временного окна *
          </label>
          <input
            type="time"
            v-model="localLocation.timeWindowEnd"
            @input="updateLocation"
            :class="[
              'block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
              !localLocation.timeWindowEnd
                ? 'border-red-300'
                : 'border-gray-300'
            ]"
          />
          <p v-if="timeWindowEndError" class="mt-1 text-xs text-red-600">
            {{ timeWindowEndError }}
          </p>
        </div>
      </div>

      <!-- Priority -->
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Приоритет посещения
        </label>
        <div class="flex space-x-3">
          <label
            v-for="priorityOption in priorityOptions"
            :key="priorityOption.value"
            class="flex items-center"
          >
            <input
              type="radio"
              v-model="localLocation.priority"
              :value="priorityOption.value"
              @change="updateLocation"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
            />
            <span class="ml-2 text-sm text-gray-700">{{
              priorityOption.label
            }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Address Preview -->
    <div class="mt-4 pt-4 border-t border-gray-200">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">Полный адрес:</span>
        <span class="text-sm text-gray-900 font-medium">{{
          getFullAddress()
        }}</span>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-sm font-medium text-gray-700">Координаты:</span>
        <span class="text-sm text-gray-500">
          {{ localLocation.latitude.toFixed(6) }},
          {{ localLocation.longitude.toFixed(6) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, reactive } from 'vue'
import type { Location } from './types'

const props = defineProps<{
  location: Location
  index: number
}>()

const emit = defineEmits<{
  update: [location: Location]
  remove: [index: number]
}>()

// Local copy for editing
const localLocation = ref<Location>({ ...props.location })

// Validation errors
const errors = reactive({
  name: '',
  city: '',
  street: '',
  houseNumber: '',
  latitude: '',
  longitude: '',
  timeWindowStart: '',
  timeWindowEnd: ''
})

// Priority options
const priorityOptions = [
  { value: 'low' as const, label: 'Низкий' },
  { value: 'medium' as const, label: 'Средний' },
  { value: 'high' as const, label: 'Высокий' }
]

// Check if this is the first location (can't be removed)
const isFirstLocation = computed(() => props.index === 0)

// Computed error messages for template
const nameError = computed(() => errors.name)
const cityError = computed(() => errors.city)
const streetError = computed(() => errors.street)
const houseNumberError = computed(() => errors.houseNumber)
const latitudeError = computed(() => errors.latitude)
const longitudeError = computed(() => errors.longitude)
const timeWindowStartError = computed(() => errors.timeWindowStart)
const timeWindowEndError = computed(() => errors.timeWindowEnd)

// Validation functions
const validateName = (name: string): string => {
  if (!name.trim()) return 'Название обязательно'
  if (name.length < 2) return 'Минимум 2 символа'
  return ''
}

const validateCity = (city: string): string => {
  if (!city.trim()) return 'Город обязателен'
  // Допускаем: буквы (в т.ч. заглавные в середине для "Большие Березники"),
  // пробелы, дефисы, точки (для сокращений).
  if (!/^[А-ЯЁа-яё][А-ЯЁа-яё\s.\-]+$/.test(city))
    return 'Введите название города русскими буквами'
  return ''
}

// Улица — необязательное поле. Валидируем только если заполнено.
const validateStreet = (street: string): string => {
  if (!street.trim()) return '' // необязательное поле
  const patterns = [
    // с типом улицы в начале: "ул. Ленина", "пр. Победы", "пер. Школьный"
    /^(ул\.|пр\.|пр-кт|пер\.|б-р|наб\.|ш\.|пл\.|туп\.|проезд|просек|тракт|бульвар|набережная|площадь|переулок|проспект|улица|шоссе)\s+.+$/i,
    // без типа, с заглавной: "Центральная", "50 лет Октября"
    /^[А-ЯЁ0-9].+$/
  ]
  if (!patterns.some((p) => p.test(street))) {
    return 'Примеры: "ул. Советская", "пр. Ленина", "Центральная"'
  }
  return ''
}

// Номер дома — необязательное поле. Валидируем только если заполнено.
const validateHouseNumber = (houseNumber: string): string => {
  if (!houseNumber.trim()) return '' // необязательное поле
  if (!/^[1-9]\d{0,4}[а-яА-Яa-zA-Z]?(\/\d+)?$/.test(houseNumber))
    return 'Примеры: 16, 101А, 11/4'
  return ''
}

const validateLatitude = (lat: number): string => {
  if (isNaN(lat)) return 'Широта должна быть числом'
  if (lat < -90 || lat > 90) return 'Широта должна быть от -90 до 90'
  return ''
}

const validateLongitude = (lng: number): string => {
  if (isNaN(lng)) return 'Долгота должна быть числом'
  if (lng < -180 || lng > 180) return 'Долгота должна быть от -180 до 180'
  return ''
}

const validateTime = (time: string, fieldName: string): string => {
  if (!time) return `${fieldName} обязательно`
  if (!/^([01]\d|2[0-3]):([0-5]\d)$/.test(time))
    return 'Некорректный формат времени'
  return ''
}

// Validate all fields
const validateLocation = (): boolean => {
  let isValid = true

  errors.name = validateName(localLocation.value.name)
  errors.city = validateCity(localLocation.value.city)
  errors.street = validateStreet(localLocation.value.street)
  errors.houseNumber = validateHouseNumber(localLocation.value.houseNumber)
  errors.latitude = validateLatitude(localLocation.value.latitude)
  errors.longitude = validateLongitude(localLocation.value.longitude)
  errors.timeWindowStart = validateTime(
    localLocation.value.timeWindowStart,
    'Время начала'
  )
  errors.timeWindowEnd = validateTime(
    localLocation.value.timeWindowEnd,
    'Время окончания'
  )

  // Check if all errors are empty
  Object.values(errors).forEach((error) => {
    if (error) isValid = false
  })

  return isValid
}

// Smart city formatting
const formatCity = (city: string): string => {
  if (!city.trim()) return city

  return city
    .split(' ')
    .map((word) => {
      // Обработка составных названий: "Санкт-Петербург"
      if (word.includes('-')) {
        return word
          .split('-')
          .map(
            (part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase()
          )
          .join('-')
      }
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    })
    .join(' ')
}

// Get full formatted address
const getFullAddress = (): string => {
  if (
    !localLocation.value.city ||
    !localLocation.value.street ||
    !localLocation.value.houseNumber
  ) {
    return 'Заполните адрес полностью'
  }

  const formattedCity = formatCity(localLocation.value.city)

  const house = localLocation.value.houseNumber.trim()

  return `г. ${formattedCity}, ${localLocation.value.street}, д. ${house}`
}

// Update parent when local data changes
const updateLocation = () => {
  // Smart formatting before emitting
  localLocation.value.city = formatCity(localLocation.value.city)

  // Validate before emitting
  validateLocation()
  emit('update', { ...localLocation.value })
}

// Watch for prop changes
watch(
  () => props.location,
  (newLocation) => {
    localLocation.value = { ...newLocation }
    validateLocation()
  },
  { deep: true }
)

// Initial validation
validateLocation()
</script>
