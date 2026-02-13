import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, VueWrapper } from '@vue/test-utils'
import DashboardView from '@/views/DashboardView.vue'
import * as api from '@/services/api'
import { createRouter, createMemoryHistory } from 'vue-router'
import { ComponentPublicInstance } from 'vue'

// Определяем тип для компонента
type DashboardViewInstance = ComponentPublicInstance<{
  handleRouteSelect: (routeId: string) => Promise<void>
  selectedRouteId: string | null
}>

// Мокаем API функции
vi.mock('@/services/api', () => ({
  fetchRoutes: vi.fn(),
  fetchRouteDetails: vi.fn(),
  fetchRouteMetrics: vi.fn(),
  getMetrics: vi.fn(),
  runBenchmark: vi.fn(),
  checkHealth: vi.fn(),
  fetchAllLocations: vi.fn()
}))

// Мокаем компоненты для простоты тестирования
vi.mock('@/components/dashboard/RouteList.vue', () => ({
  default: {
    name: 'RouteList',
    template: '<div data-testid="route-list">RouteList Mock</div>',
    props: ['routes', 'selectedRouteId'],
    emits: ['select-route']
  }
}))

vi.mock('@/components/dashboard/RouteMetrics.vue', () => ({
  default: {
    name: 'RouteMetrics',
    template: '<div data-testid="route-metrics">RouteMetrics Mock</div>',
    props: ['route', 'metrics']
  }
}))

vi.mock('@/components/dashboard/ModelComparison.vue', () => ({
  default: {
    name: 'ModelComparison',
    template: '<div data-testid="model-comparison">ModelComparison Mock</div>',
    props: ['benchmarkResults', 'isLoading']
  }
}))

vi.mock('@/components/dashboard/MetricsTable.vue', () => ({
  default: {
    name: 'MetricsTable',
    template: '<div data-testid="metrics-table">MetricsTable Mock</div>',
    props: ['metrics']
  }
}))

vi.mock('@/components/dashboard/HealthStatus.vue', () => ({
  default: {
    name: 'HealthStatus',
    template: '<div data-testid="health-status">HealthStatus Mock</div>',
    props: ['status']
  }
}))

// Создаем роутер для тестов
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/dashboard', component: DashboardView }
  ]
})

describe('DashboardView.vue', () => {
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
        locations: ['store-4', 'store-5', 'store-6'],
        total_distance_km: 45.8,
        total_time_hours: 5.7,
        total_cost_rub: 3750,
        model_used: 'deepseek',
        fallback_reason: 'Llama unavailable, using fallback',
        created_at: '2026-02-11T11:45:00Z'
      }
    ]
  }

  const mockRouteDetails = {
    id: 'route-1',
    name: 'Test Route 1',
    locations: ['store-1', 'store-2'],
    locations_sequence: ['store-2', 'store-1'],
    locations_data: [
      {
        id: 'store-1',
        name: 'Store 1',
        latitude: 55.7558,
        longitude: 37.6173,
        address: 'Address 1',
        time_window_start: '09:00',
        time_window_end: '18:00',
        priority: 1
      },
      {
        id: 'store-2',
        name: 'Store 2',
        latitude: 55.7489,
        longitude: 37.616,
        address: 'Address 2',
        time_window_start: '10:00',
        time_window_end: '19:00',
        priority: 2
      }
    ],
    total_distance_km: 10.5,
    total_time_hours: 1.5,
    total_cost_rub: 1250,
    model_used: 'llama',
    fallback_reason: null,
    created_at: '2026-02-13T09:15:00Z'
  }

  const mockRouteMetrics = {
    metrics: [
      {
        id: 'metric-1',
        route_id: 'route-1',
        model: 'llama',
        response_time_ms: 1245,
        quality_score: 0.87,
        cost_rub: 25.5,
        timestamp: '2026-02-13T09:15:30Z'
      },
      {
        id: 'metric-2',
        route_id: 'route-1',
        model: 'qwen',
        response_time_ms: 432,
        quality_score: 0.82,
        cost_rub: 0,
        timestamp: '2026-02-13T09:16:15Z'
      }
    ]
  }

  const mockAllMetrics = {
    metrics: [
      {
        id: 'metric-1',
        route_id: 'route-1',
        model: 'llama',
        response_time_ms: 1245,
        quality_score: 0.87,
        cost_rub: 25.5,
        timestamp: '2026-02-13T09:15:30Z'
      },
      {
        id: 'metric-2',
        route_id: 'route-2',
        model: 'qwen',
        response_time_ms: 432,
        quality_score: 0.82,
        cost_rub: 0,
        timestamp: '2026-02-13T09:16:15Z'
      },
      {
        id: 'metric-3',
        route_id: 'route-3',
        model: 'deepseek',
        response_time_ms: 1850,
        quality_score: 0.89,
        cost_rub: 18.0,
        timestamp: '2026-02-13T09:17:00Z'
      }
    ]
  }

  const mockHealthStatus = {
    status: 'healthy' as const,
    services: {
      database: 'connected' as const,
      qwen: 'available' as const,
      deepseek: 'available' as const,
      llama: 'connected' as const
    }
  }

  const mockBenchmarkResults = {
    total_duration_seconds: 45.2,
    results: [
      {
        model: 'llama',
        num_tests: 5,
        avg_response_time_ms: 1250,
        min_response_time_ms: 850,
        max_response_time_ms: 2100,
        avg_quality_score: 0.87,
        total_cost_rub: 250,
        success_rate: 1.0,
        timestamp: '2026-02-13T11:00:00Z'
      },
      {
        model: 'qwen',
        num_tests: 5,
        avg_response_time_ms: 450,
        min_response_time_ms: 350,
        max_response_time_ms: 650,
        avg_quality_score: 0.82,
        total_cost_rub: 0,
        success_rate: 1.0,
        timestamp: '2026-02-13T11:00:00Z'
      }
    ]
  }

  const mockLocations = [
    {
      id: 'store-1',
      name: 'Store 1',
      latitude: 55.7558,
      longitude: 37.6173,
      address: 'Address 1',
      time_window_start: '09:00',
      time_window_end: '18:00',
      priority: 1
    },
    {
      id: 'store-2',
      name: 'Store 2',
      latitude: 55.7489,
      longitude: 37.616,
      address: 'Address 2',
      time_window_start: '10:00',
      time_window_end: '19:00',
      priority: 2
    }
  ]

  beforeEach(async () => {
    vi.resetAllMocks()

    // Настраиваем моки API
    vi.mocked(api.fetchRoutes).mockResolvedValue(mockRoutes)
    vi.mocked(api.fetchRouteDetails).mockResolvedValue(mockRouteDetails)
    vi.mocked(api.fetchRouteMetrics).mockResolvedValue(mockRouteMetrics)
    vi.mocked(api.getMetrics).mockResolvedValue(mockAllMetrics)
    vi.mocked(api.runBenchmark).mockResolvedValue(mockBenchmarkResults)
    vi.mocked(api.checkHealth).mockResolvedValue(mockHealthStatus)
    vi.mocked(api.fetchAllLocations).mockResolvedValue(mockLocations)

    await router.push('/dashboard')
    await router.isReady()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('отображает заголовок и описание', () => {
    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.text()).toContain('Dashboard')
    expect(wrapper.text()).toContain('Обзор оптимизированных маршрутов')
  })

  it('отображает загрузочное состояние при начальной загрузке', () => {
    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.text()).toContain('Загрузка данных...')
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
  })

  it('загружает данные при монтировании', async () => {
    mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    expect(api.fetchRoutes).toHaveBeenCalledTimes(1)
    expect(api.getMetrics).toHaveBeenCalledTimes(2)
    expect(api.checkHealth).toHaveBeenCalledTimes(1)
    expect(api.fetchAllLocations).toHaveBeenCalledTimes(1)
    expect(api.runBenchmark).toHaveBeenCalledTimes(1)
  })

  it('отображает статус здоровья после загрузки', async () => {
    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    const healthStatus = wrapper.find('[data-testid="health-status"]')
    expect(healthStatus.exists()).toBe(true)
  })

  it('отображает статистику маршрутов', async () => {
    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Всего маршрутов')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('Среднее время')
    expect(wrapper.text()).toContain('Средняя стоимость')
  })

  it('выбирает первый маршрут по умолчанию', async () => {
    mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    expect(api.fetchRouteDetails).toHaveBeenCalledWith('route-1')
  })

  it('правильно рассчитывает средние значения', async () => {
    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('3.5 ч')
    expect(wrapper.text()).toContain('2500 ₽')
  })

  it('загружает детали маршрута при выборе маршрута', async () => {
    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<DashboardViewInstance>

    await flushPromises()

    // Сбрасываем вызовы после начальной загрузки
    vi.mocked(api.fetchRouteDetails).mockClear()
    vi.mocked(api.fetchRouteMetrics).mockClear()

    // Вызываем handleRouteSelect через vm
    await wrapper.vm.handleRouteSelect('route-2')
    await flushPromises()

    expect(api.fetchRouteDetails).toHaveBeenCalledWith('route-2')
  })

  it('отображает ошибку при неудачной загрузке', async () => {
    vi.mocked(api.fetchRoutes).mockRejectedValue(new Error('Network error'))

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Ошибка загрузки данных')
    expect(wrapper.text()).toContain('Network error')
  })

  it('позволяет перезагрузить данные при ошибке', async () => {
    vi.mocked(api.fetchRoutes)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(mockRoutes)

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    // Находим и кликаем по кнопке повторной попытки
    const retryButton = wrapper.find('button.text-red-800')
    await retryButton.trigger('click')
    await flushPromises()

    expect(api.fetchRoutes).toHaveBeenCalledTimes(2)
    expect(api.getMetrics).toHaveBeenCalledTimes(3)
    expect(api.checkHealth).toHaveBeenCalledTimes(2)
  })

  it('загружает метрики при клике на кнопку обновления', async () => {
    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    vi.mocked(api.getMetrics).mockClear()

    const refreshButton = wrapper
      .findAll('button')
      .find((b) => b.text().includes('Обновить'))
    await refreshButton?.trigger('click')
    await flushPromises()

    expect(api.getMetrics).toHaveBeenCalledTimes(1)
  })

  it('обрабатывает ошибку при загрузке деталей маршрута', async () => {
    vi.mocked(api.fetchRouteDetails).mockRejectedValue(
      new Error('Route not found')
    )

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    // Проверяем, что ошибка не крашит приложение
    expect(wrapper.find('[data-testid="route-metrics"]').exists()).toBe(true)
  })

  it('обрабатывает ошибку при загрузке бенчмарка', async () => {
    vi.mocked(api.runBenchmark).mockRejectedValue(new Error('Benchmark failed'))

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    // Проверяем, что ошибка не крашит приложение
    expect(wrapper.find('[data-testid="model-comparison"]').exists()).toBe(true)
  })

  it('корректно обновляет selectedRouteId при выборе маршрута', async () => {
    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<DashboardViewInstance>

    await flushPromises()

    expect(wrapper.vm.selectedRouteId).toBe('route-1')

    await wrapper.vm.handleRouteSelect('route-2')

    expect(wrapper.vm.selectedRouteId).toBe('route-2')
  })

  it('отображает все основные компоненты после загрузки', async () => {
    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    expect(wrapper.find('[data-testid="route-list"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="route-metrics"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="model-comparison"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="metrics-table"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="health-status"]').exists()).toBe(true)
  })
})
