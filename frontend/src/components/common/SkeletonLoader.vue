<template>
  <div
    class="animate-pulse bg-gray-200 rounded"
    :style="{ height: height, width: width }"
  ></div>
</template>

<script setup lang="ts">
defineProps<{
  height?: string
  width?: string
}>()
</script>
