<template>
  <div class="py-6 md:py-8">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-2xl md:text-3xl font-bold text-gray-900">Optimize & Test</h1>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
      <!-- Model Selection -->
      <div class="lg:col-span-2">
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-6">Model Configuration</h2>
          
          <!-- Model Selection -->
          <div class="mb-8">
            <label class="block text-sm font-medium text-gray-700 mb-3">Select Model</label>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                v-for="model in models"
                :key="model.id"
                @click="selectedModel = model.id"
                class="p-4 border rounded-lg text-left transition-all duration-200"
                :class="selectedModel === model.id 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'"
              >
                <div class="flex items-center mb-2">
                  <div :class="model.color" class="h-10 w-10 rounded-lg flex items-center justify-center mr-3">
                    <span :class="model.textColor" class="font-bold">{{ model.label }}</span>
                  </div>
                  <div>
                    <div class="font-semibold text-gray-900">{{ model.name }}</div>
                  </div>
                </div>
                <div class="text-xs text-gray-600">{{ model.description }}</div>
              </button>
            </div>
          </div>

          <!-- Parameters -->
          <div class="space-y-6">
            <div>
              
            </div>

            
          </div>
        </div>
      </div>

      <!-- Controls and Status -->
      <div class="space-y-6">
        <!-- Run Controls -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Run Test</h3>
          
          <div class="space-y-4">
            <button
              @click="runTest"
              :disabled="isRunning"
              class="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              <span v-if="!isRunning">Run Test</span>
              <span v-else class="flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Running...
              </span>
            </button>

            
          </div>
        </div>

        <!-- Status -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Test Status</h3>
          
          <div class="space-y-4">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-gray-600">Selected Model</span>
                <span class="font-medium">{{ selectedModelName }}</span>
              </div>
          

              <div class="text-sm text-gray-600 mb-2">Last Test Results</div>
                            <div  class="text-gray-500 text-sm italic">
                No tests run yet
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const models = [
  {
    id: 'gigachat',
    name: 'GigaChat',
    label: 'G',
    description: 'High-performance Russian LLM',
    color: 'bg-green-100',
    textColor: 'text-green-600'
  },
  {
    id: 'qwen',
    name: 'Qwen',
    label: 'Q',
    description: 'description for qwen',
    color: 'bg-purple-100',
    textColor: 'text-purple-600'
  },
  {
    id: 'tpro',
    name: 'T-Pro',
    label: 'T',
    description: 'desc for T',
    color: 'bg-yellow-100',
    textColor: 'text-yellow-600'
  }
]

const selectedModel = ref('gigachat')
const maxTokens = ref(512)
const temperature = ref(0.7)
const isRunning = ref(false)
//const lastResult = ref<{ responseTime: number; tokens: number } | null>(null)

const selectedModelName = computed(() => {
  return models.find(m => m.id === selectedModel.value)?.name || 'Unknown'
})

const modelStatus = {
  gigachat: { usage: 92, status: 'online' },
  cotype: { usage: 93, status: 'online' },
  tpro: { usage: 90, status: 'limited' }
}

const runTest = () => {
  isRunning.value = true
  
  // Simulate API call
  setTimeout(() => {
    isRunning.value = false
  }, 2000)
}


</script>