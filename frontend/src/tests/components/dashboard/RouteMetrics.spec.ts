import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import RouteMetrics from '@/components/dashboard/RouteMetrics.vue'
import MetricCard from '@/components/dashboard/MetricCard.vue'
import type { RouteDetails, Metric } from '@/services/api'

// Мокаем MetricCard
vi.mock('@/components/dashboard/MetricCard.vue', () => ({
  default: {
    name: 'MetricCard',
    template:
      '<div class="metric-card-mock" :data-title="title" :data-value="value"></div>',
    props: ['title', 'value', 'unit', 'color', 'loading']
  }
}))

// Мокаем SkeletonLoader
vi.mock('@/components/common/SkeletonLoader.vue', () => ({
  default: {
    name: 'SkeletonLoader',
    template: '<div class="skeleton-loader-mock"></div>',
    props: ['height', 'width']
  }
}))

describe('RouteMetrics.vue', () => {
  const mockRoute: RouteDetails = {
    id: 'route-1',
    name: 'Test Route 1',
    locations: ['store-1', 'store-2'],
    locations_sequence: ['store-2', 'store-1'],
    locations_data: [],
    total_distance_km: 10.5,
    total_time_hours: 1.5,
    total_cost_rub: 1250,
    model_used: 'llama',
    fallback_reason: null,
    created_at: '2026-02-13T09:15:00Z'
  }

  const mockMetrics: Metric[] = [
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
    },
    {
      id: 'metric-3',
      route_id: 'route-1',
      model: 'llama',
      response_time_ms: 1850,
      quality_score: 0.89,
      cost_rub: 18.0,
      timestamp: '2026-02-13T09:17:00Z'
    }
  ]

  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = mount(RouteMetrics, {
      props: {
        route: mockRoute,
        metrics: mockMetrics,
        isLoading: false
      },
      global: {
        stubs: {
          MetricCard: true,
          SkeletonLoader: true
        }
      }
    })
  })

  it('отображает информацию о выбранном маршруте', () => {
    const routeInfo = wrapper.find('.bg-gray-50.rounded-lg')
    expect(routeInfo.text()).toContain('Test Route 1')
    expect(routeInfo.text()).toContain('ID: route-1')
    expect(routeInfo.text()).toContain('Llama')
  })

  it('отображает три MetricCard с ключевыми метриками', () => {
    const metricCards = wrapper.findAllComponents(MetricCard)
    expect(metricCards.length).toBe(3)

    expect(metricCards[0].props('title')).toBe('Общее расстояние')
    expect(metricCards[0].props('value')).toBe(10.5)
    expect(metricCards[0].props('unit')).toBe('км')

    expect(metricCards[1].props('title')).toBe('Общее время')
    expect(metricCards[1].props('value')).toBe(1.5)
    expect(metricCards[1].props('unit')).toBe('часов')

    expect(metricCards[2].props('title')).toBe('Общая стоимость')
    expect(metricCards[2].props('value')).toBe(1250)
    expect(metricCards[2].props('unit')).toBe('₽')
  })

  it('отображает таблицу с метриками моделей', () => {
    const table = wrapper.find('table')
    expect(table.exists()).toBe(true)

    const rows = wrapper.findAll('tbody tr')
    expect(rows.length).toBe(3)

    // Проверяем данные первой строки (llama)
    expect(rows[0].text()).toContain('Llama')
    expect(rows[0].text()).toContain('1245 мс')
    expect(rows[0].text()).toContain('87.0%')
    expect(rows[0].text()).toContain('25.50 ₽')
  })

  it('отображает пустое состояние при отсутствии маршрута', () => {
    const emptyWrapper = mount(RouteMetrics, {
      props: {
        route: null,
        metrics: [],
        isLoading: false
      },
      global: {
        stubs: {
          MetricCard: true,
          SkeletonLoader: true
        }
      }
    })

    expect(emptyWrapper.text()).toContain('Нет данных')
    expect(emptyWrapper.text()).toContain(
      'Выберите маршрут для просмотра метрик'
    )
  })

  it('правильно форматирует дату создания маршрута', () => {
    const dateText = wrapper.find('.text-right p.text-sm.text-gray-600').text()
    expect(dateText).toMatch(/\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}/)
  })

  it('применяет правильные классы для бейджей моделей', () => {
    const badges = wrapper.findAll('span.inline-flex')

    // Первый бейдж - модель маршрута (llama), следующие - модели в таблице
    // Метрики: llama, qwen, llama — все получают цвет по своей модели
    expect(badges[1].classes()).toContain('bg-blue-100')
    expect(badges[1].classes()).toContain('text-blue-800')

    expect(badges[2].classes()).toContain('bg-purple-100')
    expect(badges[2].classes()).toContain('text-purple-800')

    expect(badges[3].classes()).toContain('bg-blue-100')
    expect(badges[3].classes()).toContain('text-blue-800')
  })

  it('правильно определяет цвет для времени ответа', async () => {
    const vm = wrapper.vm as any

    expect(vm.getResponseTimeColor(500)).toBe('bg-green-500')
    expect(vm.getResponseTimeColor(1000)).toBe('bg-yellow-500')
    expect(vm.getResponseTimeColor(2000)).toBe('bg-red-500')
  })

  it('правильно вычисляет процент времени ответа', () => {
    const vm = wrapper.vm as any

    expect(vm.getResponseTimePercentage(1000)).toBe(50)
    expect(vm.getResponseTimePercentage(2000)).toBe(100)
    expect(vm.getResponseTimePercentage(2500)).toBe(100) // ограничение
  })

  it('правильно получает название модели', () => {
    const vm = wrapper.vm as any

    expect(vm.getModelName('llama')).toBe('Llama')
    expect(vm.getModelName('qwen')).toBe('Qwen')
    expect(vm.getModelName('unknown')).toBe('unknown')
  })

  it('правильно получает классы для бейджей моделей', () => {
    const vm = wrapper.vm as any

    expect(vm.getModelBadgeClass('llama')).toBe('bg-blue-100 text-blue-800')
    expect(vm.getModelBadgeClass('qwen')).toBe('bg-purple-100 text-purple-800')
  })

  it('отображает сообщение об отсутствии метрик', () => {
    const wrapperWithoutMetrics = mount(RouteMetrics, {
      props: {
        route: mockRoute,
        metrics: [],
        isLoading: false
      },
      global: {
        stubs: {
          MetricCard: true,
          SkeletonLoader: true
        }
      }
    })

    // Должны быть только метрики маршрута, но не таблица
    const metricCards = wrapperWithoutMetrics.findAllComponents(MetricCard)
    expect(metricCards.length).toBe(3)

    const table = wrapperWithoutMetrics.find('table')
    expect(table.exists()).toBe(false)
  })

  it('обрабатывает случай с отсутствующим route', () => {
    const wrapperWithoutRoute = mount(RouteMetrics, {
      props: {
        route: null,
        metrics: mockMetrics,
        isLoading: false
      },
      global: {
        stubs: {
          MetricCard: true,
          SkeletonLoader: true
        }
      }
    })

    // Должны отображаться метрики, но не информация о маршруте
    const routeInfo = wrapperWithoutRoute.find('.bg-gray-50.rounded-lg')
    expect(routeInfo.exists()).toBe(false)

    const metricCards = wrapperWithoutRoute.findAllComponents(MetricCard)
    expect(metricCards.length).toBe(3)
    expect(metricCards[0].props('value')).toBe(0)
  })
})
