<template>
  <section class="rounded-3xl border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.14),_transparent_34%),linear-gradient(180deg,_#ffffff_0%,_#f8fafc_100%)] px-6 py-6 shadow-sm md:px-8 md:py-7">
    <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
      <div class="min-w-0">
        <p v-if="eyebrow" class="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">
          {{ eyebrow }}
        </p>
        <h1 class="mt-2 text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">
          {{ title }}
        </h1>
        <p v-if="description" class="mt-3 max-w-3xl text-sm leading-6 text-slate-600 md:text-base">
          {{ description }}
        </p>
        <div v-if="$slots.meta" class="mt-4">
          <slot name="meta" />
        </div>
      </div>

      <div v-if="$slots.actions" class="flex shrink-0 flex-wrap items-center gap-2 lg:justify-end">
        <slot name="actions" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  eyebrow?: string
}>()
</script>
