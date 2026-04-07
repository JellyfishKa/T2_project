<template>
  <div
    class="rounded-2xl border px-4 py-4 shadow-sm transition-colors"
    :class="toneClasses"
  >
    <p class="text-[11px] font-semibold uppercase tracking-[0.12em] opacity-70">
      {{ label }}
    </p>
    <p class="mt-2 text-2xl font-semibold tracking-tight">
      {{ value }}
    </p>
    <p v-if="hint" class="mt-2 text-sm opacity-75">
      {{ hint }}
    </p>
    <div v-if="$slots.default" class="mt-3">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  label: string
  value: string | number
  hint?: string
  tone?: 'neutral' | 'blue' | 'green' | 'amber' | 'slate'
}>(), {
  tone: 'neutral',
})

const toneClasses = computed(() => {
  switch (props.tone) {
    case 'blue':
      return 'border-blue-200 bg-blue-50 text-blue-950'
    case 'green':
      return 'border-emerald-200 bg-emerald-50 text-emerald-950'
    case 'amber':
      return 'border-amber-200 bg-amber-50 text-amber-950'
    case 'slate':
      return 'border-slate-200 bg-slate-100 text-slate-950'
    default:
      return 'border-slate-200 bg-white text-slate-950'
  }
})
</script>
