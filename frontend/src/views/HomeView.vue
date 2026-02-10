<template>
  <div class="py-6 md:py-8 lg:py-12">
    <!-- Hero Section -->
    <div class="text-center mb-10 md:mb-16">
      <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
        T2 Розничная сеть
      </h1>
      <p class="text-lg md:text-xl text-gray-600 max-w-3xl mx-auto">
        Комплексная платформа на основе искусственного интеллекта для
        оптимизации маршрутов магазинов и сетевой аналитики с использованием
        нескольких LLM-моделей (GigaChat, Cotype, T-Pro).
      </p>
    </div>

    <!-- Quick Actions -->
    <div
      class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8"
    >
      <h2 class="text-2xl font-bold text-gray-900 mb-6">Навигация</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <router-link
          to="/dashboard"
          class="bg-blue-50 hover:bg-blue-100 text-blue-700 p-4 rounded-lg text-center transition-colors duration-200"
        >
          <div class="text-lg font-semibold mb-1">Dashboard</div>
        </router-link>

        <router-link
          to="/optimize"
          class="bg-green-50 hover:bg-green-100 text-green-700 p-4 rounded-lg text-center transition-colors duration-200"
        >
          <div class="text-lg font-semibold mb-1">Test Models</div>
        </router-link>

        <router-link
          to="/optimize"
          class="bg-yellow-50 hover:bg-yellow-100 text-yellow-700 p-4 rounded-lg text-center transition-colors duration-200"
        >
          <div class="text-lg font-semibold mb-1">Optimize</div>
        </router-link>

        <router-link
          to="/analytics"
          class="bg-purple-50 hover:bg-purple-100 text-purple-700 p-4 rounded-lg text-center transition-colors duration-200"
        >
          <div class="text-lg font-semibold mb-1">Analytics</div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts"></script>
