import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import DashboardView from '@/views/DashboardView.vue'
import * as api from '@/services/api'

// Мокаем API
vi.mock('@/services/api', () => ({
  fetchRoutes: vi.fn(),
  fetchRouteDetails: vi.fn(),
  fetchMetrics: vi.fn(),
  runBenchmark: vi.fn(),
  checkHealth: vi.fn(),
  fetchAllLocations: vi.fn()
}))

describe('DashboardView.vue', () => {
  const mockRoutes = {
    total: 3,
    items: [
      {
        id: 'route-1',
        name: 'Test Route 1',
        locations: ['store-1'],
        total_distance_km: 10,
        total_time_hours: 1,
        total_cost_rub: 100,
        model_used: 'llama',
        created_at: '2024-01-06T09:15:00Z'
      }
    ]
  }

  const mockRouteDetails = {
    id: 'route-1',
    name: 'Test Route 1',
    locations: ['store-1'],
    locations_sequence: ['store-1'],
    locations_data: [],
    total_distance_km: 10,
    total_time_hours: 1,
    total_cost_rub: 100,
    model_used: 'llama',
    created_at: '2024-01-06T09:15:00Z'
  }

  const mockHealthStatus = {
    status: 'healthy' as const,
    services: {
      database: 'connected' as const,
      llama: 'connected' as const,
      qwen: 'available' as const,
      tpro: 'unavailable' as const
    }
  }

  beforeEach(() => {
    vi.resetAllMocks()

    // Настраиваем моки
    vi.mocked(api.fetchRoutes).mockResolvedValue(mockRoutes)
    vi.mocked(api.fetchRouteDetails).mockResolvedValue(mockRouteDetails)
    vi.mocked(api.fetchMetrics).mockResolvedValue({ metrics: [] })
    vi.mocked(api.runBenchmark).mockResolvedValue({
      total_duration_seconds: 30,
      results: []
    })
    vi.mocked(api.checkHealth).mockResolvedValue(mockHealthStatus)
    vi.mocked(api.fetchAllLocations).mockResolvedValue([])
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('отображает заголовок и описание', () => {
    const wrapper = mount(DashboardView)

    expect(wrapper.text()).toContain('Dashboard')
    expect(wrapper.text()).toContain('Обзор оптимизированных маршрутов')
  })

  it('отображает загрузочное состояние', () => {
    const wrapper = mount(DashboardView)

    expect(wrapper.text()).toContain('Загрузка данных...')
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
  })

  it('отображает статус здоровья', async () => {
    const wrapper = mount(DashboardView)
    await flushPromises()

    expect(wrapper.text()).toContain('Система работает нормально')
    expect(wrapper.text()).toContain('Все системы работают')
  })

  it('отображает статистику маршрутов', async () => {
    const wrapper = mount(DashboardView)
    await flushPromises()

    expect(wrapper.text()).toContain('Всего маршрутов')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('Среднее время')
    expect(wrapper.text()).toContain('Средняя стоимость')
  })

  it('отображает ошибку при неудачной загрузке', async () => {
    vi.mocked(api.fetchRoutes).mockRejectedValue(new Error('Network error'))

    const wrapper = mount(DashboardView)
    await flushPromises()

    expect(wrapper.text()).toContain('Ошибка загрузки данных')
    expect(wrapper.text()).toContain('Network error')
  })

  it('позволяет перезагрузить данные при ошибке', async () => {
    vi.mocked(api.fetchRoutes)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(mockRoutes)

    const wrapper = mount(DashboardView)
    await flushPromises()

    // Кликаем по кнопке повторной попытки
    const retryButton = wrapper.find('button.text-red-800')
    await retryButton.trigger('click')
    await flushPromises()

    expect(api.fetchRoutes).toHaveBeenCalledTimes(2)
  })

  it('выбирает первый маршрут по умолчанию', async () => {
    const wrapper = mount(DashboardView)
    await flushPromises()

    expect(api.fetchRouteDetails).toHaveBeenCalledWith('route-1')
  })

  it('правильно рассчитывает средние значения', async () => {
    vi.mocked(api.fetchRoutes).mockResolvedValue({
      total: 2,
      items: [
        {
          id: 'route-1',
          name: 'Route 1',
          locations: ['store-1'],
          total_distance_km: 10,
          total_time_hours: 1,
          total_cost_rub: 100,
          model_used: 'llama',
          created_at: '2024-01-06T09:15:00Z'
        },
        {
          id: 'route-2',
          name: 'Route 2',
          locations: ['store-2'],
          total_distance_km: 30,
          total_time_hours: 3,
          total_cost_rub: 300,
          model_used: 'qwen',
          created_at: '2024-01-06T09:15:00Z'
        }
      ]
    })

    const wrapper = mount(DashboardView)
    await flushPromises()

    // Среднее время: (1 + 3) / 2 = 2.0
    expect(wrapper.text()).toContain('2.0 ч')
    // Средняя стоимость: (100 + 300) / 2 = 200
    expect(wrapper.text()).toContain('200 ₽')
  })
})
