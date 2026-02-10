<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <Header @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />

    <div class="flex">
      <!-- Sidebar для десктопа -->
      <Sidebar
        :is-open="isSidebarOpen"
        @close="isSidebarOpen = false"
        class="hidden lg:block"
      />

      <!-- Mobile Sidebar (overlay) -->
      <div
        v-if="isSidebarOpen"
        class="fixed inset-0 z-40 lg:hidden"
        @click="isSidebarOpen = false"
      >
        <div class="fixed inset-0 bg-gray-600 bg-opacity-75"></div>
      </div>

      <Transition
        enter-active-class="transition ease-in-out duration-300 transform"
        enter-from-class="-translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transition ease-in-out duration-300 transform"
        leave-from-class="translate-x-0"
        leave-to-class="-translate-x-full"
      >
        <Sidebar
          v-if="isSidebarOpen"
          :is-open="isSidebarOpen"
          @close="isSidebarOpen = false"
          class="fixed inset-y-0 left-0 z-50 w-64 lg:hidden"
        />
      </Transition>

      <!-- Main Content -->
      <main class="flex-1 p-4 md:p-6 lg:p-8">
        <div class="mx-auto max-w-7xl">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Header from './Header.vue'
import Sidebar from './Sidebar.vue'

const isSidebarOpen = ref(false)

// Закрываем sidebar при нажатии Escape
const handleEscape = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && isSidebarOpen.value) {
    isSidebarOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleEscape)
})
</script>
