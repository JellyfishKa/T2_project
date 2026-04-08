<template>
  <div class="bg-white border border-gray-200 rounded-lg p-3 min-w-0">
    <p class="text-xs font-medium text-gray-600 truncate">{{ title }}</p>
    <div v-if="loading" class="mt-2">
      <SkeletonLoader height="28px" width="100%" />
    </div>
    <p v-else class="mt-1 text-xl font-semibold text-gray-900 truncate">
      {{ formattedValue }}
      <span class="text-sm font-normal text-gray-600">{{ unit }}</span>
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'

const props = defineProps<{
  title: string
  value: number
  unit: string
  color: 'blue' | 'green' | 'purple' | 'yellow' | 'red'
  loading?: boolean
}>()

const formattedValue = computed(() => {
  if (props.value % 1 === 0) {
    return props.value.toFixed(0)
  }
  return props.value.toFixed(1)
})
</script>
