<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Ограничения</h3>
    
    <div class="space-y-6">
      <!-- Vehicle Capacity (1-4) -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label for="vehicleCapacity" class="text-sm font-medium text-gray-700">
            Вместимость машины
          </label>
          <span class="text-sm text-gray-500">{{ localConstraints.vehicleCapacity }} ед.</span>
        </div>
        <input
          type="range"
          id="vehicleCapacity"
          v-model.number="localConstraints.vehicleCapacity"
          min="1"
          max="4"
          step="1"
          @input="updateConstraints"
          class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-600"
        />
        <div class="flex justify-between text-xs text-gray-500 mt-1">
          <span>1</span>
          <span>2</span>
          <span>3</span>
          <span>4</span>
        </div>
        <p class="mt-1 text-xs text-gray-500">
          Количество пассажирских мест в машине
        </p>
      </div>

      <!-- Max Distance -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label for="maxDistance" class="text-sm font-medium text-gray-700">
            Макс. расстояние
          </label>
          <span class="text-sm text-gray-500">{{ localConstraints.maxDistance }} км</span>
        </div>
        <input
          type="range"
          id="maxDistance"
          v-model.number="localConstraints.maxDistance"
          min="50"
          max="1000"
          step="50"
          @input="updateConstraints"
          class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-600"
        />
        <div class="flex justify-between text-xs text-gray-500 mt-1">
          <span>50</span>
          <span>500</span>
          <span>1000</span>
        </div>
      </div>

      <!-- Time Windows -->
      <div class="space-y-4">
        <div>
          <label for="startTime" class="block text-sm font-medium text-gray-700 mb-1">
            Время начала маршрута
          </label>
          <input
            type="time"
            id="startTime"
            v-model="localConstraints.startTime"
            @input="updateConstraints"
            class="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>
        
        <div>
          <label for="endTime" class="block text-sm font-medium text-gray-700 mb-1">
            Время окончания маршрута
          </label>
          <input
            type="time"
            id="endTime"
            v-model="localConstraints.endTime"
            @input="updateConstraints"
            class="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>
      </div>

      <!-- Max Stops -->
      <div>
        <label for="maxStops" class="block text-sm font-medium text-gray-700 mb-2">
          Макс. количество остановок (опционально)
        </label>
        <input
          type="number"
          id="maxStops"
          v-model.number="localConstraints.maxStops"
          min="2"
          max="50"
          @input="updateConstraints"
          class="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          placeholder="Не ограничено"
        />
      </div>

      <!-- Forbidden Roads -->
      <div>
        <label for="forbiddenRoads" class="block text-sm font-medium text-gray-700 mb-2">
          Запрещенные дороги (через запятую)
        </label>
        <textarea
          id="forbiddenRoads"
          v-model="forbiddenRoadsInput"
          @input="updateForbiddenRoads"
          rows="2"
          class="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          placeholder="МКАД, ТТК, Садовое кольцо"
        />
        <div v-if="localConstraints.forbiddenRoads && localConstraints.forbiddenRoads.length > 0" class="mt-2">
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(road, index) in localConstraints.forbiddenRoads"
              :key="index"
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
            >
              {{ road }}
              <button
                @click="removeForbiddenRoad(index)"
                class="ml-1 text-red-600 hover:text-red-800"
              >
                ×
              </button>
            </span>
          </div>
        </div>
      </div>

      <!-- Reset Button -->
      <div class="pt-4 border-t border-gray-200">
        <button
          type="button"
          @click="resetConstraints"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Сбросить ограничения
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import type { Constraints } from './types'

const props = defineProps<{
  constraints: Constraints
}>()

const emit = defineEmits<{
  'update-constraints': [constraints: Constraints]
}>()

// Local state - ИНИЦИАЛИЗИРУЕМ значения по умолчанию
const localConstraints = reactive<Constraints>({
  vehicleCapacity: props.constraints.vehicleCapacity || 1,  // Изменено с 100 на 1
  maxDistance: props.constraints.maxDistance || 500,
  startTime: props.constraints.startTime || '08:00',
  endTime: props.constraints.endTime || '20:00',
  maxStops: props.constraints.maxStops,
  forbiddenRoads: props.constraints.forbiddenRoads || []
})

const forbiddenRoadsInput = ref(props.constraints.forbiddenRoads?.join(', ') || '')

// Update constraints and notify parent
const updateConstraints = () => {
  emit('update-constraints', { ...localConstraints })
}

// Handle forbidden roads input
const updateForbiddenRoads = () => {
  if (!forbiddenRoadsInput.value.trim()) {
    localConstraints.forbiddenRoads = []
  } else {
    localConstraints.forbiddenRoads = forbiddenRoadsInput.value
      .split(',')
      .map(road => road.trim())
      .filter(road => road.length > 0)
  }
  updateConstraints()
}

// Remove a forbidden road
const removeForbiddenRoad = (index: number) => {
  if (localConstraints.forbiddenRoads) {
    localConstraints.forbiddenRoads.splice(index, 1)
    forbiddenRoadsInput.value = localConstraints.forbiddenRoads.join(', ')
    updateConstraints()
  }
}

// Reset constraints to defaults
const resetConstraints = () => {
  localConstraints.vehicleCapacity = 1  // Изменено с 100 на 1
  localConstraints.maxDistance = 500
  localConstraints.startTime = '08:00'
  localConstraints.endTime = '20:00'
  localConstraints.maxStops = undefined
  localConstraints.forbiddenRoads = []
  forbiddenRoadsInput.value = ''
  updateConstraints()
}

// Watch for prop changes
watch(() => props.constraints, (newConstraints) => {
  localConstraints.vehicleCapacity = newConstraints.vehicleCapacity || 1
  localConstraints.maxDistance = newConstraints.maxDistance || 500
  localConstraints.startTime = newConstraints.startTime || '08:00'
  localConstraints.endTime = newConstraints.endTime || '20:00'
  localConstraints.maxStops = newConstraints.maxStops
  localConstraints.forbiddenRoads = newConstraints.forbiddenRoads || []
  forbiddenRoadsInput.value = newConstraints.forbiddenRoads?.join(', ') || ''
}, { deep: true })
</script>