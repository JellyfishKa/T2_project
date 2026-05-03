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
  metricsSortField: string
  metricsSortDirection: 'asc' | 'desc'
  routeSortField: string
  routeSortDirection: 'asc' | 'desc'
}>

// Мокаем API функции
vi.mock('@/services/api', () => ({
  fetchRoutes: vi.fn(),
  fetchRouteDetails: vi.fn(),
  fetchRouteComparison: vi.fn(),
  getMetrics: vi.fn(),
  compareModels: vi.fn(),
  checkHealth: vi.fn(),
  getApiErrorMessage: vi.fn((err: unknown) => err instanceof Error ? err.message : String(err))
}))

// Мокаем компоненты
vi.mock('@/components/dashboard/RouteList.vue', () => ({
  default: {
    name: 'RouteList',
    template:
      '<div data-testid="route-list">RouteList Mock<button data-testid="select-route-button" @click="$emit(\'select-route\', \'route-1\')">Select</button><button data-testid="compare-route-button" @click="$emit(\'compare-route\', \'route-1\')">Compare</button></div>',
    props: [
      'routes',
      'isLoading',
      'selectedRouteId',
      'sortable',
      'sortField',
      'sortDirection'
    ],
    emits: ['select-route', 'compare-route', 'sort']
  }
}))

vi.mock('@/components/dashboard/RouteCompareModal.vue', () => ({
  default: {
    name: 'RouteCompareModal',
    template: '<div data-testid="route-compare-modal" :data-open="String(open)">RouteCompareModal Mock</div>',
    props: ['open', 'comparison', 'routeName', 'isLoading', 'error'],
    emits: ['close']
  }
}))

vi.mock('@/components/dashboard/RouteMetrics.vue', () => ({
  default: {
    name: 'RouteMetrics',
    template: '<div data-testid="route-metrics">RouteMetrics Mock</div>',
    props: ['route', 'metrics', 'isLoading']
  }
}))

vi.mock('@/components/dashboard/ModelComparison.vue', () => ({
  default: {
    name: 'ModelComparison',
    template: '<div data-testid="model-comparison">ModelComparison Mock</div>',
    props: ['benchmarkResults', 'recommendations', 'isLoading']
  }
}))

vi.mock('@/components/dashboard/MetricsTable.vue', () => ({
  default: {
    name: 'MetricsTable',
    template: '<div data-testid="metrics-table">MetricsTable Mock</div>',
    props: ['metrics', 'isLoading', 'sortable', 'sortField', 'sortDirection'],
    emits: ['sort']
  }
}))

vi.mock('@/components/dashboard/HealthStatus.vue', () => ({
  default: {
    name: 'HealthStatus',
    template: '<div data-testid="health-status">HealthStatus Mock</div>',
    props: ['status']
  }
}))

vi.mock('@/components/common/SkeletonLoader.vue', () => ({
  default: {
    name: 'SkeletonLoader',
    template: '<div class="skeleton-loader"></div>'
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
        has_comparison: true,
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
        has_comparison: false,
        created_at: '2026-02-12T14:30:00Z'
      },
      {
        id: 'route-3',
        name: 'Test Route 3',
        locations: ['store-4', 'store-5', 'store-6'],
        total_distance_km: 45.8,
        total_time_hours: 5.7,
        total_cost_rub: 3750,
        model_used: 'llama',
        fallback_reason: null,
        has_comparison: false,
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
        lat: 55.7558,
        lon: 37.6173,
        address: 'Address 1',
        time_window_start: '09:00',
        time_window_end: '18:00',
        category: 'A' as const,
        city: null,
        district: null
      },
      {
        id: 'store-2',
        name: 'Store 2',
        lat: 55.7489,
        lon: 37.616,
        address: 'Address 2',
        time_window_start: '10:00',
        time_window_end: '19:00',
        category: 'B' as const,
        city: null,
        district: null
      }
    ],
    total_distance_km: 10.5,
    total_time_hours: 1.5,
    total_cost_rub: 1250,
    model_used: 'llama',
    fallback_reason: null,
    has_comparison: true,
    created_at: '2026-02-13T09:15:00Z'
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
        model: 'llama',
        response_time_ms: 1850,
        quality_score: 0.89,
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
      }
    ],
    recommendations: [
      {
        scenario: 'Быстрые запросы',
        recommended_model: 'qwen',
        reason: 'Бесплатно и очень быстро'
      }
    ]
  }

  const mockHealthStatus = {
    status: 'healthy' as const,
    services: {
      database: 'connected' as const,
      qwen: 'available' as const,
      llama: 'loaded' as const
    }
  }

  const mockRouteComparison = {
    route_id: 'route-1',
    original: [
      { id: 'store-1', name: 'Store 1', lat: 55.7558, lon: 37.6173, order: 1, address: null, category: 'A' }
    ],
    current: [
      { id: 'store-1', name: 'Store 1', lat: 55.7558, lon: 37.6173, order: 1, address: null, category: 'A' }
    ],
    diff: {
      distance_delta_km: -1.2,
      time_delta_hours: -0.2,
      cost_delta_rub: -120,
      changed_stops_count: 1,
      improvement_percentage: 8.4
    },
    model_used: 'llama',
    created_at: '2026-02-13T09:15:00Z'
  }

  let wrapper: VueWrapper<DashboardViewInstance>

  beforeEach(async () => {
    vi.resetAllMocks()

    vi.mocked(api.fetchRoutes).mockResolvedValue(mockRoutes)
    vi.mocked(api.fetchRouteDetails).mockResolvedValue(mockRouteDetails)
    vi.mocked(api.getMetrics).mockResolvedValue(mockAllMetrics)
    vi.mocked(api.compareModels).mockResolvedValue(mockModelComparison)
    vi.mocked(api.checkHealth).mockResolvedValue(mockHealthStatus)
    vi.mocked(api.fetchRouteComparison).mockResolvedValue(mockRouteComparison)
    vi.mocked(api.getApiErrorMessage).mockImplementation((err: unknown) =>
      err instanceof Error ? err.message : String(err)
    )

    await router.push('/dashboard')
    await router.isReady()

    wrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<DashboardViewInstance>
  })

  afterEach(() => {
    vi.clearAllMocks()
    wrapper.unmount()
  })

  it('загружает данные с backend при монтировании', async () => {
    await flushPromises()

    expect(api.fetchRoutes).toHaveBeenCalledWith(0, 100)
    expect(api.compareModels).toHaveBeenCalled()
    expect(api.checkHealth).toHaveBeenCalled()
    expect(api.getMetrics).toHaveBeenCalled()
  })

  it('отображает ошибку при неудачной загрузке', async () => {
    vi.mocked(api.fetchRoutes).mockRejectedValue(new Error('Network error'))

    wrapper.unmount()

    const errorWrapper = mount(DashboardView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    expect(errorWrapper.text()).toContain('Ошибка загрузки данных')
    expect(errorWrapper.text()).toContain('Network error')
  })

  it('выбирает первый маршрут по умолчанию', async () => {
    await flushPromises()

    expect(api.fetchRouteDetails).toHaveBeenCalledWith('route-1')
  })

  it('обновляет все данные при клике на кнопку обновления', async () => {
    await flushPromises()

    vi.mocked(api.fetchRoutes).mockClear()
    vi.mocked(api.compareModels).mockClear()
    vi.mocked(api.checkHealth).mockClear()
    vi.mocked(api.getMetrics).mockClear()

    // Находим кнопку обновления по тексту
    const buttons = wrapper.findAll('button')
    const refreshButton = buttons.find((b) => b.text().includes('Обновить все'))
    expect(refreshButton).toBeDefined()

    await refreshButton!.trigger('click')
    await flushPromises()

    expect(api.fetchRoutes).toHaveBeenCalled()
    expect(api.compareModels).toHaveBeenCalled()
    expect(api.checkHealth).toHaveBeenCalled()
    expect(api.getMetrics).toHaveBeenCalled()
  })

  it('отображает кнопку обновления с состоянием загрузки', async () => {
    await flushPromises()

    const buttons = wrapper.findAll('button')
    const refreshButton = buttons.find((b) => b.text().includes('Обновить все'))
    expect(refreshButton).toBeDefined()

    await refreshButton!.trigger('click')

    expect(refreshButton!.attributes('disabled')).toBeDefined()
    expect(refreshButton!.text()).toContain('Обновление...')

    await flushPromises()

    expect(refreshButton!.attributes('disabled')).toBeUndefined()
    expect(refreshButton!.text()).toContain('Обновить все')
  })

  it('обрабатывает сортировку маршрутов', async () => {
    await flushPromises()

    // Проверяем, что свойства сортировки существуют
    expect(wrapper.vm.routeSortField).toBeDefined()
    expect(wrapper.vm.routeSortDirection).toBeDefined()
  })

  it('обрабатывает сортировку метрик', async () => {
    await flushPromises()

    // Проверяем, что свойства сортировки метрик существуют
    expect(wrapper.vm.metricsSortField).toBeDefined()
    expect(wrapper.vm.metricsSortDirection).toBeDefined()
  })

  it('компонент MetricsTable получает правильные пропсы', async () => {
    await flushPromises()

    const metricsTable = wrapper.findComponent({ name: 'MetricsTable' })
    expect(metricsTable.exists()).toBe(true)
    expect(metricsTable.props('sortable')).toBe(true)
    expect(metricsTable.props('sortField')).toBe(wrapper.vm.metricsSortField)
    expect(metricsTable.props('sortDirection')).toBe(
      wrapper.vm.metricsSortDirection
    )
  })

  it('компонент RouteList получает правильные пропсы', async () => {
    await flushPromises()

    const routeList = wrapper.findComponent({ name: 'RouteList' })
    expect(routeList.exists()).toBe(true)
    expect(routeList.props('sortable')).toBe(true)
    expect(routeList.props('sortField')).toBe(wrapper.vm.routeSortField)
    expect(routeList.props('sortDirection')).toBe(wrapper.vm.routeSortDirection)
  })

  it('открывает модалку сравнения маршрута', async () => {
    await flushPromises()

    await wrapper.get('[data-testid="compare-route-button"]').trigger('click')
    await flushPromises()

    expect(api.fetchRouteComparison).toHaveBeenCalledWith('route-1')
    const compareModal = wrapper.findComponent({ name: 'RouteCompareModal' })
    expect(compareModal.props('open')).toBe(true)
  })
})
