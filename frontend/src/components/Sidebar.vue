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
        <span class="ml-3 text-lg font-semibold text-gray-900">Menu</span>
      </div>
      <button
        @click="$emit('close')"
        class="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-600 hover:bg-gray-100"
      >
        <span class="sr-only">Close sidebar</span>
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
        <!-- Иконки как встроенные SVG -->
        <div
          class="mr-3 h-5 w-5 flex-shrink-0"
          :class="
            isActive(item.to)
              ? 'text-blue-500'
              : 'text-gray-400 group-hover:text-blue-500'
          "
        >
          <svg
            v-if="item.name === 'Home'"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
            />
          </svg>
          <svg
            v-else-if="item.name === 'Dashboard'"
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
          <svg
            v-else-if="item.name === 'Optimize'"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <svg v-else fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
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

interface NavigationItem {
  name: string
  to: string
}

const navigation: NavigationItem[] = [
  { name: 'Home', to: '/' },
  { name: 'Dashboard', to: '/dashboard' },
  { name: 'Optimize', to: '/optimize' },
  { name: 'Analytics', to: '/analytics' }
]

const route = useRoute()

const isActive = (path: string): boolean => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>
