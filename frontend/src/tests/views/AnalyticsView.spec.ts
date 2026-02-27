import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, VueWrapper } from '@vue/test-utils'
import AnalyticsView from '@/views/AnalyticsView.vue'
import * as api from '@/services/api'
import { createRouter, createMemoryHistory } from 'vue-router'

// Мокаем API
vi.mock('@/services/api', () => ({
  fetchRoutes: vi.fn(),
  getMetrics: vi.fn(),
  compareModels: vi.fn(),
  getInsights: vi.fn(),
  downloadScheduleExcel: vi.fn(),
  importScheduleExcel: vi.fn(),
}))

// Мокаем Chart.js компоненты
// AnalyticsView импортирует { Bar as BarChart, Scatter as ScatterChart, Line as LineChart }
vi.mock('vue-chartjs', () => ({
  Bar: {
    name: 'BarChart',
    template: '<div data-testid="bar-chart" class="mock-bar-chart"></div>'
  },
  Scatter: {
    name: 'ScatterChart',
    template:
      '<div data-testid="scatter-chart" class="mock-scatter-chart"></div>'
  },
  Line: {
    name: 'LineChart',
    template: '<div data-testid="line-chart" class="mock-line-chart"></div>'
  }
}))

vi.mock('@/components/common/SkeletonLoader.vue', () => ({
  default: {
    name: 'SkeletonLoader',
    template:
      '<div data-testid="skeleton-loader" class="skeleton-loader"></div>'
  }
}))

// Создаем роутер
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/analytics', component: AnalyticsView }
  ]
})

describe('AnalyticsView.vue', () => {
  const mockRoutes = {
    total: 3,
    items: [
      {
        id: 'route-1',
        name: 'Test Route 1',
        locations: ['store-1', 'store-2'],
        total_distance_km: 10.5,
        total_time_hours: 1.5,
        total_cost_rub: 1250,
        model_used: 'llama',
        fallback_reason: null,
        created_at: '2026-02-13T09:15:00Z'
      },
      {
        id: 'route-2',
        name: 'Test Route 2',
        locations: ['store-3'],
        total_distance_km: 25.3,
        total_time_hours: 3.2,
        total_cost_rub: 2500,
        model_used: 'qwen',
        fallback_reason: null,
        created_at: '2026-02-12T14:30:00Z'
      },
      {
        id: 'route-3',
        name: 'Test Route 3',
        locations: ['store-4', 'store-5'],
        total_distance_km: 45.8,
        total_time_hours: 5.7,
        total_cost_rub: 3750,
        model_used: 'llama',
        fallback_reason: null,
        created_at: '2026-02-11T11:45:00Z'
      }
    ]
  }

  const mockMetrics = {
    metrics: [
      {
        id: 'metric-1',
        route_id: 'route-1',
        model: 'llama',
        response_time_ms: 1245,
        quality_score: 87.0,
        cost_rub: 25.5,
        timestamp: '2026-02-13T09:15:30Z'
      },
      {
        id: 'metric-2',
        route_id: 'route-2',
        model: 'qwen',
        response_time_ms: 432,
        quality_score: 82.0,
        cost_rub: 0,
        timestamp: '2026-02-13T09:16:15Z'
      },
      {
        id: 'metric-3',
        route_id: 'route-3',
        model: 'llama',
        response_time_ms: 1850,
        quality_score: 89.0,
        cost_rub: 18.0,
        timestamp: '2026-02-13T09:17:00Z'
      }
    ]
  }

  const mockModelComparison = {
    models: [
      {
        name: 'llama',
        avg_response_time_ms: 1250,
        avg_quality_score: 0.87,
        total_cost_rub: 250,
        success_rate: 0.95,
        usage_count: 100
      },
      {
        name: 'qwen',
        avg_response_time_ms: 450,
        avg_quality_score: 0.82,
        total_cost_rub: 0,
        success_rate: 0.99,
        usage_count: 200
      },
    ],
    recommendations: []
  }

  let wrapper: VueWrapper<any>

  beforeEach(async () => {
    vi.resetAllMocks()

    vi.mocked(api.fetchRoutes).mockResolvedValue(mockRoutes)
    vi.mocked(api.getMetrics).mockResolvedValue(mockMetrics)
    vi.mocked(api.compareModels).mockResolvedValue(mockModelComparison)
    vi.mocked(api.getInsights).mockResolvedValue(null as any)
    vi.mocked(api.downloadScheduleExcel).mockResolvedValue(undefined)
    vi.mocked(api.importScheduleExcel).mockResolvedValue({ updated: 0, skipped: 0, errors: [] })

    await router.push('/analytics')
    await router.isReady()

    wrapper = mount(AnalyticsView, {
      global: {
        plugins: [router],
        stubs: {
          BarChart: true,
          ScatterChart: true,
          LineChart: true,
          SkeletonLoader: true
        }
      }
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    wrapper.unmount()
  })

  it('загружает данные при монтировании', async () => {
    await flushPromises()

    expect(api.fetchRoutes).toHaveBeenCalledWith(0, 100)
    expect(api.getMetrics).toHaveBeenCalled()
    expect(api.compareModels).toHaveBeenCalled()
  })

  it('отображает статистические карточки после загрузки', async () => {
    await flushPromises()

    expect(wrapper.text()).toContain('Всего маршрутов')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('Среднее расстояние')
    expect(wrapper.text()).toContain('27.2 км')
    expect(wrapper.text()).toContain('Средняя стоимость')
    expect(wrapper.text()).toContain('2500 ₽')
    expect(wrapper.text()).toContain('Среднее качество')
    expect(wrapper.text()).toContain('86.0%')
  })

  it('отображает графики после загрузки', async () => {
    await flushPromises()

    // Ищем компоненты графиков по их наличию в DOM
    const barChart = wrapper.findComponent({ name: 'BarChart' })
    const scatterChart = wrapper.findComponent({ name: 'ScatterChart' })
    const lineChart = wrapper.findComponent({ name: 'LineChart' })

    expect(barChart.exists()).toBe(true)
    expect(scatterChart.exists()).toBe(true)
    expect(lineChart.exists()).toBe(true)
  })

  it('правильно рассчитывает статистику по моделям', async () => {
    await flushPromises()

    // Проверяем наличие названий моделей в таблице
    expect(wrapper.text()).toContain('Llama')
    expect(wrapper.text()).toContain('Qwen')
    // Таблица отображает агрегированные средние, а не индивидуальные значения:
    // llama: (1245+1850)/2 = 1548, qwen: 432/1 = 432
    expect(wrapper.text()).toContain('1548')
    expect(wrapper.text()).toContain('432')
  })

  it('отображает ошибку при неудачной загрузке', async () => {
    vi.mocked(api.fetchRoutes).mockRejectedValue(new Error('Network error'))

    // Пересоздаем wrapper с ошибкой
    const errorWrapper = mount(AnalyticsView, {
      global: {
        plugins: [router],
        stubs: {
          BarChart: true,
          ScatterChart: true,
          LineChart: true,
          SkeletonLoader: true
        }
      }
    })

    await flushPromises()

    expect(errorWrapper.text()).toContain('Ошибка загрузки данных')
    expect(errorWrapper.text()).toContain('Network error')
  })

  it('позволяет обновить данные при клике на кнопку', async () => {
    await flushPromises()

    // Очищаем вызовы после начальной загрузки
    vi.mocked(api.fetchRoutes).mockClear()
    vi.mocked(api.getMetrics).mockClear()
    vi.mocked(api.compareModels).mockClear()

    // Находим кнопку обновления по тексту и кликаем
    const refreshButton = wrapper
      .findAll('button')
      .find((b) => b.text().includes('Обновить'))
    expect(refreshButton).toBeDefined()

    await refreshButton?.trigger('click')
    await flushPromises()

    expect(api.fetchRoutes).toHaveBeenCalled()
    expect(api.getMetrics).toHaveBeenCalled()
    expect(api.compareModels).toHaveBeenCalled()
  })

  it('отображает пустое состояние при отсутствии данных', async () => {
    vi.mocked(api.fetchRoutes).mockResolvedValue({ total: 0, items: [] })
    vi.mocked(api.getMetrics).mockResolvedValue({ metrics: [] })

    const emptyWrapper = mount(AnalyticsView, {
      global: {
        plugins: [router],
        stubs: {
          BarChart: true,
          ScatterChart: true,
          LineChart: true,
          SkeletonLoader: true
        }
      }
    })

    await flushPromises()

    expect(emptyWrapper.text()).toContain('Нет данных для отображения')
  })

  it('правильно форматирует названия моделей', async () => {
    await flushPromises()

    const vm = wrapper.vm as any
    expect(vm.getModelName('llama')).toBe('Llama')
    expect(vm.getModelName('qwen')).toBe('Qwen')
    expect(vm.getModelName('unknown')).toBe('unknown')
  })

  it('правильно применяет классы для бейджей моделей', async () => {
    await flushPromises()

    const vm = wrapper.vm as any
    expect(vm.getModelBadgeClass('llama')).toBe('bg-blue-100 text-blue-800')
    expect(vm.getModelBadgeClass('qwen')).toBe('bg-purple-100 text-purple-800')
  })

  it('корректно строит данные для scatter plot', async () => {
    await flushPromises()

    const vm = wrapper.vm as any
    const scatterData = vm.scatterData

    expect(scatterData.datasets[0].data).toHaveLength(3)
    expect(scatterData.datasets[0].data[0]).toHaveProperty('x', 10.5)
    expect(scatterData.datasets[0].data[0]).toHaveProperty('y', 1250)
  })

  it('корректно строит данные для временного ряда', async () => {
    await flushPromises()

    const vm = wrapper.vm as any
    const timeSeriesData = vm.timeSeriesData

    expect(timeSeriesData.labels).toHaveLength(3)
    expect(timeSeriesData.datasets[0].data).toHaveLength(3)
  })
})
