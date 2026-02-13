<template>
  <div class="space-y-4">
    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-4">
      <div
        class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"
      ></div>
      <p class="mt-2 text-sm text-gray-600">
        Загрузка результатов бенчмарка...
      </p>
    </div>

    <!-- Comparison Charts -->
    <div v-else-if="benchmarkResults.length > 0" class="space-y-6">
      <!-- Response Time Comparison -->
      <div>
        <h4 class="text-sm font-medium text-gray-900 mb-3">
          Время ответа (мс)
        </h4>
        <div class="space-y-3">
          <div
            v-for="result in benchmarkResults"
            :key="result.model"
            class="flex items-center"
          >
            <div class="w-24 text-sm font-medium text-gray-900">
              {{ getModelName(result.model) }}
            </div>
            <div class="flex-1">
              <div class="flex items-center">
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div
                    class="h-3 rounded-full"
                    :class="getResponseTimeColor(result.avg_response_time_ms)"
                    :style="{
                      width:
                        getResponseTimeWidth(result.avg_response_time_ms) + '%'
                    }"
                  ></div>
                </div>
                <div
                  class="ml-3 text-sm font-medium text-gray-900 w-16 text-right"
                >
                  {{ result.avg_response_time_ms }}
                </div>
              </div>
              <div class="text-xs text-gray-500 mt-1">
                Min: {{ result.min_response_time_ms }} | Max:
                {{ result.max_response_time_ms }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quality Score Comparison -->
      <div>
        <h4 class="text-sm font-medium text-gray-900 mb-3">
          Качество решения (%)
        </h4>
        <div class="space-y-3">
          <div
            v-for="result in benchmarkResults"
            :key="result.model"
            class="flex items-center"
          >
            <div class="w-24 text-sm font-medium text-gray-900">
              {{ getModelName(result.model) }}
            </div>
            <div class="flex-1">
              <div class="flex items-center">
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div
                    class="bg-green-500 h-3 rounded-full"
                    :style="{ width: result.avg_quality_score * 100 + '%' }"
                  ></div>
                </div>
                <div
                  class="ml-3 text-sm font-medium text-gray-900 w-16 text-right"
                >
                  {{ (result.avg_quality_score * 100).toFixed(1) }}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Cost Comparison -->
      <div>
        <h4 class="text-sm font-medium text-gray-900 mb-3">Стоимость (₽)</h4>
        <div class="space-y-3">
          <div
            v-for="result in benchmarkResults"
            :key="result.model"
            class="flex items-center"
          >
            <div class="w-24 text-sm font-medium text-gray-900">
              {{ getModelName(result.model) }}
            </div>
            <div class="flex-1">
              <div class="flex items-center">
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div
                    class="bg-purple-500 h-3 rounded-full"
                    :style="{
                      width: getCostWidth(result.total_cost_rub) + '%'
                    }"
                  ></div>
                </div>
                <div
                  class="ml-3 text-sm font-medium text-gray-900 w-16 text-right"
                >
                  {{ result.total_cost_rub.toFixed(2) }} ₽
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Success Rate -->
      <div>
        <h4 class="text-sm font-medium text-gray-900 mb-3">
          Успешность выполнения
        </h4>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div
            v-for="result in benchmarkResults"
            :key="result.model"
            class="bg-gray-50 rounded-lg p-3"
          >
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-900">{{
                getModelName(result.model)
              }}</span>
              <span
                class="text-sm font-semibold"
                :class="getSuccessRateColor(result.success_rate)"
              >
                {{ (result.success_rate * 100).toFixed(0) }}%
              </span>
            </div>
            <div class="mt-2 text-xs text-gray-500">
              {{ result.num_tests }} тестов выполнено
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-8 border rounded-lg border-gray-200">
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
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">
        Нет результатов бенчмарка
      </h3>
      <p class="mt-1 text-sm text-gray-500">
        Запустите бенчмарк для сравнения моделей
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { BenchmarkResult } from '@/services/api'

defineProps<{
  benchmarkResults: BenchmarkResult[]
  isLoading?: boolean
}>()

const getModelName = (model: string): string => {
  const modelMap: Record<string, string> = {
    llama: 'llama',
    qwen: 'Qwen',
    DeepSeek: 'DeepSeek'
  }
  return modelMap[model] || model
}

const getResponseTimeColor = (responseTime: number): string => {
  if (responseTime < 800) return 'bg-green-500'
  if (responseTime < 1500) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getResponseTimeWidth = (responseTime: number): number => {
  // Нормализуем до 2000 мс = 100%
  return Math.min((responseTime / 2000) * 100, 100)
}

const getCostWidth = (cost: number): number => {
  // Нормализуем до 300 ₽ = 100%
  return Math.min((cost / 300) * 100, 100)
}

const getSuccessRateColor = (rate: number): string => {
  if (rate >= 0.95) return 'text-green-600'
  if (rate >= 0.85) return 'text-yellow-600'
  return 'text-red-600'
}
</script>
