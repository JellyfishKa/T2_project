<template>
  <div class="space-y-8 py-6 md:py-8">
    <PageHero
      eyebrow="Т2.Логист"
      title="Т2.Логист"
      description="Комплексная платформа на основе искусственного интеллекта для оптимизации маршрутов магазинов и сетевой аналитики с использованием нескольких LLM-моделей."
    >
      <template #meta>
        <div class="flex flex-wrap gap-2">
          <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">Маршруты</span>
          <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">Расписание</span>
          <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">Аналитика</span>
          <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">База данных</span>
        </div>
      </template>
      <template #actions>
        <button
          type="button"
          class="inline-flex items-center rounded-full bg-blue-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700"
          @click="goToOptimize"
        >
          Начать оптимизацию
        </button>
      </template>
    </PageHero>

    <div class="grid gap-4 md:grid-cols-3">
      <InfoStatCard label="Главный сценарий" value="Оптимизация → расписание" hint="Сначала строим маршрут, затем применяем и сравниваем." tone="blue" />
      <InfoStatCard label="Контроль качества" value="LLM + метрики" hint="ИИ помогает выбрать маршрут, метрики подтверждают результат." tone="green" />
      <InfoStatCard label="Режим работы" value="Без перегрузки" hint="Каждый экран показывает сначала главное, детали раскрываются по мере необходимости." tone="amber" />
    </div>

    <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-8">
      <div class="flex items-center justify-between gap-3 flex-wrap mb-6">
        <div>
          <h2 class="text-2xl font-semibold text-slate-950">Навигация</h2>
          <p class="mt-1 text-sm text-slate-600">
            Короткий путь по основным сценариям, без лишних переходов.
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div
          v-for="item in quickActions"
          :key="item.title"
          class="group relative rounded-2xl border border-slate-200 p-5 transition-all hover:-translate-y-0.5 hover:border-blue-200 hover:bg-blue-50/50 hover:shadow-sm"
        >
          <router-link :to="item.to" class="absolute inset-0 z-10 rounded-2xl">
            <span class="sr-only">{{ item.title }}</span>
          </router-link>
          <div class="flex items-center justify-between gap-3">
            <div class="rounded-2xl px-3 py-2 text-sm font-semibold" :class="item.badgeClass">
              {{ item.short }}
            </div>
            <span class="text-slate-300 transition-colors group-hover:text-blue-500">→</span>
          </div>
          <h3 class="mt-4 text-lg font-semibold text-slate-950">{{ item.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-slate-600">{{ item.description }}</p>
        </div>
      </div>
    </section>

    <section class="grid gap-4 lg:grid-cols-3">
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
        <h2 class="text-lg font-semibold text-slate-950">Как работать с системой</h2>
        <div class="mt-4 grid gap-3 md:grid-cols-3">
          <div v-for="step in workflowSteps" :key="step.title" class="rounded-2xl bg-slate-50 p-4">
            <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{{ step.index }}</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">{{ step.title }}</p>
            <p class="mt-2 text-sm text-slate-600">{{ step.description }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-slate-950 p-5 text-white shadow-sm">
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-300">Рекомендация</p>
        <h2 class="mt-2 text-lg font-semibold">Начинайте с маршрута, а не с отчёта</h2>
        <p class="mt-3 text-sm leading-6 text-slate-300">
          Самый понятный путь для пользователя: сначала собрать и проверить маршрут, затем перенести его в расписание и только потом смотреть аналитику изменений.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import PageHero from '@/components/common/PageHero.vue'
import InfoStatCard from '@/components/common/InfoStatCard.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const quickActions = [
  {
    title: 'Дашборд',
    short: '01',
    to: '/dashboard',
    description: 'Быстрый обзор маршрутов, моделей и текущего состояния сервиса.',
    badgeClass: 'bg-blue-100 text-blue-700',
  },
  {
    title: 'Тест моделей',
    short: '02',
    to: '/optimize',
    description: 'Проверьте маршрут, сравните варианты и выберите лучший порядок точек.',
    badgeClass: 'bg-emerald-100 text-emerald-700',
  },
  {
    title: 'Оптимизация',
    short: '03',
    to: '/optimize',
    description: 'Постройте рабочий маршрут и вручную донастройте его перед сохранением.',
    badgeClass: 'bg-amber-100 text-amber-700',
  },
  {
    title: 'Аналитика',
    short: '04',
    to: '/analytics',
    description: 'Оцените качество решений и влияние маршрутов на операционные показатели.',
    badgeClass: 'bg-violet-100 text-violet-700',
  },
]

const workflowSteps = [
  {
    index: 'Шаг 1',
    title: 'Соберите точки и ограничения',
    description: 'Добавьте магазины, временные окна и ключевые ограничения маршрута.',
  },
  {
    index: 'Шаг 2',
    title: 'Сравните варианты и примените',
    description: 'Проверьте маршрут ИИ, вручную перестройте его и примените лучший порядок.',
  },
  {
    index: 'Шаг 3',
    title: 'Проверьте расписание и аналитику',
    description: 'Убедитесь, что изменения понятны сотрудникам и подтверждаются метриками.',
  },
]

function goToOptimize() {
  void router.push('/optimize')
}
</script>
