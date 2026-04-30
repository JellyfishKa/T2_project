<template>
  <header class="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
    <div class="px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo and mobile menu button -->
        <div class="flex items-center">
          <!-- Mobile menu button -->
          <button
            @click="$emit('toggle-sidebar')"
            class="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-900"
          >
            <span class="sr-only">Открыть меню</span>
            <svg
              class="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>

          <!-- Logo -->
          <div class="flex items-center ml-4 lg:ml-0">
            <div class="flex-shrink-0">
              <div
                class="h-9 w-9 rounded-xl bg-slate-950 flex items-center justify-center shadow-sm"
              >
                <span class="text-white font-bold text-sm">T2</span>
              </div>
            </div>
            <div class="ml-3">
              <div class="flex items-center gap-2">
                <h1 class="text-lg font-semibold text-slate-950 md:text-xl">T2 Платформа</h1>
                <span class="hidden rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700 sm:inline-flex">
                  Рабочая зона
                </span>
              </div>
              <p class="text-xs text-slate-500 hidden sm:block">
                Маршруты, расписание и аналитика без лишнего шума
              </p>
            </div>
          </div>
        </div>

        <!-- Desktop Navigation -->
        <nav class="hidden lg:flex lg:items-center lg:space-x-2">
          <router-link
            v-for="item in navigation"
            :key="item.name"
            :to="item.to"
            class="px-3 py-2 rounded-full text-sm font-medium transition-colors duration-200 text-slate-600 hover:text-blue-700 hover:bg-blue-50"
            :class="{ 'text-blue-700 bg-blue-50': isActive(item.to) }"
          >
            {{ item.name }}
          </router-link>
        </nav>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const emit = defineEmits(['toggle-sidebar'])

const navigation = [
  { name: 'Главная', to: '/' },
  { name: 'Дашборд', to: '/dashboard' },
  { name: 'Оптимизация', to: '/optimize' },
  { name: 'Расписание', to: '/schedule' },
  { name: 'Аналитика', to: '/analytics' },
  { name: 'База данных', to: '/database' },
]

const route = useRoute()

const isActive = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>
