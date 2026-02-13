<template>
  <div class="py-6 md:py-8">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-2xl md:text-3xl font-bold text-gray-900">
        Оптимизация маршрута
      </h1>
      <p class="mt-2 text-gray-600">
        Настройте параметры и запустите оптимизацию маршрута с использованием
        выбранной LLM модели
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
      <!-- Main Form -->
      <div class="lg:col-span-2 space-y-6">
        <OptimizationForm
          ref="optimizationForm"
          @submit="handleSubmit"
          @validate="handleValidation"
        />

        <!-- File Upload Component -->
        <FileUpload @add-locations="handleAddLocationsFromFile" />
      </div>

      <!-- Side Panel -->
      <div class="space-y-6">
        <!-- Model Selection -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Выбор модели</h3>

          <div class="space-y-3">
            <label
              v-for="model in models"
              :key="model.id"
              class="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              :class="
                selectedModel === model.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200'
              "
            >
              <input
                type="radio"
                v-model="selectedModel"
                :value="model.id"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              />
              <div class="ml-3">
                <div class="flex items-center">
                  <div
                    :class="model.color"
                    class="h-8 w-8 rounded-lg flex items-center justify-center mr-2"
                  >
                    <span :class="model.textColor" class="font-bold">{{
                      model.label
                    }}</span>
                  </div>
                  <div>
                    <div class="text-sm font-medium text-gray-900">
                      {{ model.name }}
                    </div>
                    <div class="text-xs text-gray-500">
                      {{ model.description }}
                    </div>
                  </div>
                </div>
              </div>
            </label>
          </div>

          <div class="mt-4 pt-4 border-t border-gray-200">
            <h4 class="text-sm font-medium text-gray-900 mb-2">
              Характеристики моделей
            </h4>
            <ul class="space-y-2 text-sm text-gray-600">
              <li class="flex items-center">
                <svg
                  class="h-4 w-4 text-green-500 mr-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
                Llama: Высокая точность, платный
              </li>
              <li class="flex items-center">
                <svg
                  class="h-4 w-4 text-green-500 mr-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
                Qwen: Быстрый, бесплатный
              </li>
              <li class="flex items-center">
                <svg
                  class="h-4 w-4 text-green-500 mr-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
                DeepSeek: Баланс цены и качества
              </li>
            </ul>
          </div>
        </div>

        <!-- Constraints Summary -->
        <ConstraintsPanel
          :constraints="constraints"
          @update-constraints="handleConstraintsUpdate"
        />
      </div>
    </div>

    <!-- Form Actions -->
    <div
      class="mt-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
    >
      <div class="text-sm text-gray-600">
        <p>Все поля обязательны для заполнения</p>
        <p class="mt-1">Минимум 2 магазина для оптимизации маршрута</p>
      </div>
      <div class="flex space-x-3">
        <button
          type="button"
          @click="resetForm"
          class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Сбросить
        </button>
        <button
          type="button"
          @click="handleOptimize"
          :disabled="!isFormValid"
          class="px-6 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Оптимизировать маршрут
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import OptimizationForm from '@/components/optimize/OptimizationForm.vue'
import ConstraintsPanel from '@/components/optimize/ConstraintsPanel.vue'
import FileUpload from '@/components/optimize/FileUpload.vue'
import type { Constraints, Location } from '@/components/optimize/types'

// Models
const models = [
  {
    id: 'llama',
    name: 'Llama',
    label: 'L',
    description: 'Высокая точность, платный',
    color: 'bg-green-100',
    textColor: 'text-green-600'
  },
  {
    id: 'qwen',
    name: 'Qwen',
    label: 'Q',
    description: 'Быстрый, бесплатный',
    color: 'bg-purple-100',
    textColor: 'text-purple-600'
  },
  {
    id: 'DeepSeek',
    name: 'DeepSeek',
    label: 'D',
    description: 'Баланс цены и качества',
    color: 'bg-blue-100',
    textColor: 'text-blue-600'
  }
]

// State
const selectedModel = ref('llama')
const constraints = ref<Constraints>({
  vehicleCapacity: 1,
  maxDistance: 500,
  startTime: '08:00',
  endTime: '20:00'
})
const isFormValid = ref(false)
const optimizationForm = ref<any>(null)

// Computed
const selectedModelName = computed(() => {
  return models.find((m) => m.id === selectedModel.value)?.name || 'Llama'
})

// Methods
const handleSubmit = (formData: any) => {
  console.log('Form submitted:', {
    ...formData,
    model: selectedModel.value,
    modelName: selectedModelName.value,
    constraints: constraints.value
  })
}

const handleValidation = (isValid: boolean) => {
  isFormValid.value = isValid
}

const handleConstraintsUpdate = (updatedConstraints: Constraints) => {
  constraints.value = updatedConstraints
  console.log('Constraints updated:', constraints.value)
}

const handleAddLocationsFromFile = async (locations: Location[]) => {
  if (optimizationForm.value && locations.length > 0) {
    // Clear existing form locations first
    optimizationForm.value.clearAllLocations()

    // Wait for DOM update
    await nextTick()

    // Add all locations starting from FIRST position
    locations.forEach((location) => {
      optimizationForm.value.addLocationFromImport(location)
    })

    console.log(
      `Added ${locations.length} locations from file, starting from position 1`
    )

    // Show success message
    alert(`Успешно добавлено ${locations.length} магазинов из файла`)
  }
}

const handleOptimize = () => {
  if (!isFormValid.value) {
    alert('Пожалуйста, заполните все обязательные поля формы')
    return
  }

  if (!optimizationForm.value) {
    alert('Ошибка формы')
    return
  }

  const formData = optimizationForm.value.getFormData()

  const optimizationRequest = {
    routeName: formData.routeName,
    locations: formData.locations,
    model: selectedModel.value,
    constraints: constraints.value,
    timestamp: new Date().toISOString()
  }

  console.log('Starting optimization:', optimizationRequest)
  alert(
    `Запуск оптимизации через ${selectedModelName.value}...\n(В Неделе 2 будет отправка на backend)`
  )
}

const resetForm = () => {
  if (optimizationForm.value) {
    optimizationForm.value.resetForm()
  }
  selectedModel.value = 'llama'
  constraints.value = {
    vehicleCapacity: 1,
    maxDistance: 500,
    startTime: '08:00',
    endTime: '20:00'
  }
  console.log('Form reset')
}
</script>
