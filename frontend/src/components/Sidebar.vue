<template>
  <div class="flex h-full flex-col bg-white border-r border-gray-200">
    <!-- Sidebar header -->
    <div
      class="flex h-16 items-center justify-between px-6 border-b border-gray-200"
    >
      <div class="flex items-center">
        <div
          class="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center"
        >
          <span class="text-white font-bold text-lg">T2</span>
        </div>
        <span class="ml-3 text-lg font-semibold text-gray-900">Меню</span>
      </div>
      <button
        @click="$emit('close')"
        class="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-600 hover:bg-gray-100"
      >
        <span class="sr-only">Закрыть меню</span>
        <!-- Close icon -->
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
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 space-y-1 px-4 py-6">
      <router-link
        v-for="item in navigation"
        :key="item.name"
        :to="item.to"
        @click="$emit('close')"
        class="flex items-center px-4 py-3 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg group transition-colors duration-200"
        :class="{ 'text-blue-600 bg-blue-50': isActive(item.to) }"
      >
        <!-- Иконка пункта меню (один <svg> с подстановкой пути) -->
        <div
          class="mr-3 h-5 w-5 flex-shrink-0"
          :class="
            isActive(item.to)
              ? 'text-blue-500'
              : 'text-gray-400 group-hover:text-blue-500'
          "
        >
          <svg
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              :d="iconPaths[item.icon]"
            />
          </svg>
        </div>
        <span class="font-medium">{{ item.name }}</span>
      </router-link>
    </nav>

    <!-- Footer -->
    <div class="border-t border-gray-200 p-4">
      <div class="flex items-center"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

defineEmits(['close'])

type IconKey = 'home' | 'grid' | 'bolt' | 'chart-line' | 'calendar' | 'users'

interface NavigationItem {
  name: string
  to: string
  icon: IconKey
}

const navigation: NavigationItem[] = [
  { name: 'Главная',     to: '/',          icon: 'home' },
  { name: 'Дашборд',     to: '/dashboard', icon: 'grid' },
  { name: 'Оптимизация', to: '/optimize',  icon: 'bolt' },
  { name: 'Аналитика',   to: '/analytics', icon: 'chart-line' },
  { name: 'Расписание',  to: '/schedule',  icon: 'calendar' },
  { name: 'Сотрудники',  to: '/reps',      icon: 'users' },
]

// Heroicons-outline path data (MIT license).
const iconPaths: Record<IconKey, string> = {
  home: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
  grid: 'M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z',
  bolt: 'M13 10V3L4 14h7v7l9-11h-7z',
  'chart-line': 'M3 3v18h18M7 15l4-4 4 4 5-6',
  calendar: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  users: 'M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-5.13a4 4 0 11-8 0 4 4 0 018 0zm6 0a4 4 0 11-8 0 4 4 0 018 0z',
}

const route = useRoute()

const isActive = (path: string): boolean => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>
