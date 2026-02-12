import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MetricsTable from '@/components/dashboard/MetricsTable.vue'
import type { Metric } from '@/services/api'

describe('MetricsTable.vue', () => {
  const mockMetrics: Metric[] = [
    {
      id: 'metric-1',
      route_id: 'route-1',
      model: 'llama',
      response_time_ms: 1245,
      quality_score: 0.87,
      cost_rub: 25.5,
      timestamp: '2024-01-06T09:15:30Z'
    },
    {
      id: 'metric-2',
      route_id: 'route-2',
      model: 'qwen',
      response_time_ms: 432,
      quality_score: 0.82,
      cost_rub: 0.0,
      timestamp: '2024-01-06T09:16:15Z'
    }
  ]

  it('отображает таблицу на десктопе', () => {
    const wrapper = mount(MetricsTable, {
      props: { metrics: mockMetrics }
    })

    // Проверяем заголовки
    expect(wrapper.text()).toContain('Модель')
    expect(wrapper.text()).toContain('Маршрут')
    expect(wrapper.text()).toContain('Время ответа')
    expect(wrapper.text()).toContain('Качество')
    expect(wrapper.text()).toContain('Стоимость')
    expect(wrapper.text()).toContain('Время')

    // Проверяем данные
    expect(wrapper.text()).toContain('Llama')
    expect(wrapper.text()).toContain('route-1')
    expect(wrapper.text()).toContain('1245 мс')
    expect(wrapper.text()).toContain('87.0%')
    expect(wrapper.text()).toContain('25.50 ₽')
  })

  it('отображает пустое состояние при отсутствии метрик', () => {
    const wrapper = mount(MetricsTable, {
      props: { metrics: [] }
    })

    expect(wrapper.text()).toContain('Нет метрик')
    expect(wrapper.text()).toContain(
      'Запустите оптимизацию для создания метрик'
    )
  })

  it('отображает мобильные карточки на маленьких экранах', () => {
    // Имитируем маленький экран
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375
    })

    const wrapper = mount(MetricsTable, {
      props: { metrics: mockMetrics },
      global: {
        mocks: {
          $screen: { sm: false }
        }
      }
    })

    // Проверяем, что есть div для мобильных карточек
    expect(wrapper.find('.sm\\:hidden').exists()).toBe(true)
    expect(wrapper.text()).toContain('Маршрут:')
    expect(wrapper.text()).toContain('Время ответа:')
    expect(wrapper.text()).toContain('Качество:')
    expect(wrapper.text()).toContain('Стоимость:')
  })

  it('правильно переводит названия моделей', () => {
    const wrapper = mount(MetricsTable, {
      props: {
        metrics: [
          {
            id: 'metric-1',
            route_id: 'route-1',
            model: 'llama',
            response_time_ms: 1000,
            quality_score: 0.9,
            cost_rub: 10,
            timestamp: '2024-01-06T09:15:30Z'
          },
          {
            id: 'metric-2',
            route_id: 'route-2',
            model: 'qwen',
            response_time_ms: 500,
            quality_score: 0.8,
            cost_rub: 0,
            timestamp: '2024-01-06T09:16:00Z'
          },
          {
            id: 'metric-3',
            route_id: 'route-3',
            model: 'tpro',
            response_time_ms: 1500,
            quality_score: 0.95,
            cost_rub: 20,
            timestamp: '2024-01-06T09:17:00Z'
          }
        ]
      }
    })

    expect(wrapper.text()).toContain('Llama')
    expect(wrapper.text()).toContain('Qwen')
    expect(wrapper.text()).toContain('T-Pro')
  })
})
