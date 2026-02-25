<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200">
    <div class="px-6 py-5 border-b border-gray-200">
      <h3 class="text-lg font-semibold text-gray-900">Параметры маршрута</h3>
      <p class="mt-1 text-sm text-gray-600">
        Заполните информацию о маршруте и магазинах
      </p>
    </div>

    <form @submit.prevent="handleSubmit" class="px-6 py-5 space-y-6">
      <!-- Route Name -->
      <div>
        <label
          for="routeName"
          class="block text-sm font-medium text-gray-700 mb-2"
        >
          Название маршрута *
        </label>
        <input
          type="text"
          id="routeName"
          v-model="formData.routeName"
          @input="validateForm"
          :class="[
            'block w-full px-3 py-2 border rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            errors.routeName ? 'border-red-300' : 'border-gray-300'
          ]"
          placeholder="Например: Центральный маршрут, Маршрут №1"
        />
        <p v-if="errors.routeName" class="mt-2 text-sm text-red-600">
          {{ errors.routeName }}
        </p>
      </div>

      <!-- Locations Section -->
      <div>
        <div class="flex items-center justify-between mb-4">
          <div>
            <h4 class="text-sm font-medium text-gray-900">Магазины *</h4>
            <p class="text-sm text-gray-500">
              Минимум 2 магазина для оптимизации
            </p>
          </div>
          <button
            type="button"
            @click="addLocation"
            class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-lg text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg
              class="h-4 w-4 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            Добавить магазин
          </button>
        </div>

        <!-- Location Inputs -->
        <div class="space-y-4">
          <LocationInput
            v-for="(location, index) in formData.locations"
            :key="location.id"
            :location="location"
            :index="index"
            @update="updateLocation(index, $event)"
            @remove="removeLocation(index)"
          />
        </div>

        <!-- Location Errors -->
        <div v-if="errors.locations" class="mt-3">
          <div class="flex items-center text-sm text-red-600">
            <svg class="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clip-rule="evenodd"
              />
            </svg>
            {{ errors.locations }}
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="formData.locations.length === 0"
          class="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg"
        >
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
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">Нет магазинов</h3>
          <p class="mt-1 text-sm text-gray-500">
            Добавьте первый магазин для оптимизации маршрута
          </p>
        </div>
      </div>

      <!-- Notes -->
      <div>
        <label for="notes" class="block text-sm font-medium text-gray-700 mb-2">
          Примечания
        </label>
        <textarea
          id="notes"
          v-model="formData.notes"
          rows="3"
          class="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          placeholder="Дополнительные требования или комментарии..."
        />
        <p class="mt-2 text-sm text-gray-500">
          Необязательное поле для дополнительной информации
        </p>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import LocationInput from './LocationInput.vue'
import type { OptimizationFormData, Location } from './types'

const emit = defineEmits<{
  submit: [formData: OptimizationFormData]
  validate: [isValid: boolean]
}>()

// Form State
const formData = reactive<OptimizationFormData>({
  routeName: '',
  locations: [
    {
      id: generateId(),
      name: '',
      city: 'Саранск',
      street: '',
      houseNumber: '',
      latitude: 54.1871,
      longitude: 45.1749,
      timeWindowStart: '09:00',
      timeWindowEnd: '18:00',
      priority: 'medium'
    },
    {
      id: generateId(),
      name: '',
      city: 'Саранск',
      street: '',
      houseNumber: '',
      latitude: 54.1902,
      longitude: 45.1685,
      timeWindowStart: '09:00',
      timeWindowEnd: '18:00',
      priority: 'medium'
    }
  ],
  notes: ''
})

// Validation State
const errors = reactive({
  routeName: '',
  locations: ''
})

// Helper Functions
function generateId(): string {
  return `loc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// Methods
const addLocation = () => {
  formData.locations.push({
    id: generateId(),
    name: '',
    city: 'Саранск',
    street: '',
    houseNumber: '',
    latitude: 54.1871 + (Math.random() - 0.5) * 0.02,
    longitude: 45.1749 + (Math.random() - 0.5) * 0.02,
    timeWindowStart: '09:00',
    timeWindowEnd: '18:00',
    priority: 'medium'
  })
  validateForm()
}

const updateLocation = (index: number, updatedLocation: Location) => {
  formData.locations[index] = updatedLocation
  validateForm()
}

const removeLocation = (index: number) => {
  formData.locations.splice(index, 1)
  validateForm()
}

const validateForm = (): boolean => {
  let isValid = true

  // Reset errors
  errors.routeName = ''
  errors.locations = ''

  if (!formData.routeName.trim()) {
    errors.routeName = 'Название маршрута обязательно'
    isValid = false
  } else if (formData.routeName.length < 2) {
    errors.routeName = 'Название должно быть не менее 2 символов'
    isValid = false
  }

  // Validate locations
  if (formData.locations.length < 2) {
    errors.locations = 'Добавьте минимум 2 магазина'
    isValid = false
  } else {
    // Обязательные: name, city, timeWindowStart, timeWindowEnd, координаты.
    // street и houseNumber — опциональны (координаты достаточны для маршрута).
    const hasInvalidLocation = formData.locations.some((loc) => {
      return (
        !loc.name.trim() ||
        !loc.city.trim() ||
        !loc.timeWindowStart ||
        !loc.timeWindowEnd
      )
    })

    if (hasInvalidLocation) {
      errors.locations = 'Заполните название, город и временные окна для каждого магазина'
      isValid = false
    }
  }

  emit('validate', isValid)
  return isValid
}

const handleSubmit = () => {
  if (validateForm()) {
    // Форматируем адреса перед отправкой
    const formattedLocations = formData.locations.map((loc) => ({
      ...loc,
      address: `г. ${loc.city}, ул. ${loc.street}, д. ${loc.houseNumber}`
    }))

    emit('submit', {
      ...formData,
      locations: formattedLocations
    })
  }
}

const resetForm = () => {
  formData.routeName = ''
  formData.locations = [
    {
      id: generateId(),
      name: '',
      city: 'Саранск',
      street: '',
      houseNumber: '',
      latitude: 54.1871,
      longitude: 45.1749,
      timeWindowStart: '09:00',
      timeWindowEnd: '18:00',
      priority: 'medium'
    },
    {
      id: generateId(),
      name: '',
      city: 'Саранск',
      street: '',
      houseNumber: '',
      latitude: 54.1902,
      longitude: 45.1685,
      timeWindowStart: '09:00',
      timeWindowEnd: '18:00',
      priority: 'medium'
    }
  ]
  formData.notes = ''
  errors.routeName = ''
  errors.locations = ''
  emit('validate', false)
}

const getFormData = (): OptimizationFormData => {
  const formattedLocations = formData.locations.map((loc) => ({
    ...loc,
    address: `г. ${loc.city}, ул. ${loc.street}, д. ${loc.houseNumber}`
  }))

  return {
    ...formData,
    locations: formattedLocations
  }
}

const addLocationFromImport = (locationData: Location) => {
  formData.locations.push({
    id: locationData.id || generateId(),
    name: locationData.name,
    city: locationData.city,
    street: locationData.street,
    houseNumber: locationData.houseNumber,
    latitude: locationData.latitude,
    longitude: locationData.longitude,
    timeWindowStart: locationData.timeWindowStart || '09:00',
    timeWindowEnd: locationData.timeWindowEnd || '18:00',
    priority: locationData.priority || 'medium'
  })
  validateForm()
}

const clearAllLocations = () => {
  formData.locations = []
  validateForm()
}

defineExpose({
  resetForm,
  getFormData,
  validateForm,
  addLocationFromImport,
  clearAllLocations
})
</script>
