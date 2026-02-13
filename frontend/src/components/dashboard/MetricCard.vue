<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4">
    <div class="flex items-center">
      <div class="ml-4">
        <p class="text-sm font-medium text-gray-600">{{ title }}</p>
        <p class="text-2xl font-semibold text-gray-900">
          {{ formattedValue }}
          <span class="text-lg font-normal text-gray-600">{{ unit }}</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  value: number
  unit: string
  color: 'blue' | 'green' | 'purple' | 'yellow' | 'red'
}>()

const formattedValue = computed(() => {
  if (props.value % 1 === 0) {
    return props.value.toFixed(0)
  }
  return props.value.toFixed(1)
})

const colorClasses = computed(() => {
  const colorMap = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  }
  return colorMap[props.color] || 'bg-gray-500'
})
</script>
