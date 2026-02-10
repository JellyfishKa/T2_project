<template>
  <div class="bg-white border rounded-lg p-4" :class="borderColor">
    <div class="flex items-center">
      <div class="flex-shrink-0">
        <div class="h-10 w-10 rounded-full flex items-center justify-center" :class="statusColor">
          <svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path 
              v-if="status.status === 'healthy'" 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              stroke-width="2" 
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
            <path 
              v-else 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              stroke-width="2" 
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5z" 
            />
          </svg>
        </div>
      </div>
      <div class="ml-4 flex-1">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-medium text-gray-900">
              {{ statusTitle }}
            </h3>
            <p class="text-sm text-gray-600">Статус сервисов</p>
          </div>
          <div class="text-right">
            <p class="text-sm font-medium" :class="statusTextColor">
              {{ status.status === 'healthy' ? 'Все системы работают' : 'Есть проблемы' }}
            </p>
          </div>
        </div>
        
        <!-- Services Status -->
        <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          <div 
            v-for="(statusValue, service) in status.services" 
            :key="service"
            class="flex items-center"
          >
            <div class="h-2 w-2 rounded-full mr-2" :class="getServiceStatusColor(statusValue)"></div>
            <span class="text-sm capitalize">{{ service }}</span>
            <span class="ml-2 text-xs text-gray-500">{{ getServiceStatusText(statusValue) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed } from 'vue'
import type { HealthStatus } from '@/services/api'

const props = defineProps<{
  status: HealthStatus
}>()

const statusTitle = computed(() => {
  return props.status.status === 'healthy' ? 'Система работает нормально' : 'Обнаружены проблемы'
})

const statusColor = computed(() => {
  return props.status.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
})

const statusTextColor = computed(() => {
  return props.status.status === 'healthy' ? 'text-green-600' : 'text-red-600'
})

const borderColor = computed(() => {
  return props.status.status === 'healthy' ? 'border-green-200' : 'border-red-200'
})

const getServiceStatusColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    'connected': 'bg-green-500',
    'available': 'bg-blue-500',
    'disconnected': 'bg-red-500',
    'unavailable': 'bg-yellow-500',
    'error': 'bg-red-500'
  }
  return colorMap[status] || 'bg-gray-500'
}

const getServiceStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    'connected': 'Подключено',
    'available': 'Доступно',
    'disconnected': 'Отключено',
    'unavailable': 'Недоступно',
    'error': 'Ошибка'
  }
  return textMap[status] || status
}
</script>