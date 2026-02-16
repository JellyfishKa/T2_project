import { describe, it, expect, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import OptimizationResult from '@/components/optimize/OptimizationResult.vue'
import type { Route } from '@/services/types'

describe('OptimizationResult.vue', () => {
  const mockRoute: Route = {
    id: 'route-123',
    name: 'Optimized Test Route',
    locations: ['loc-1', 'loc-2', 'loc-3'],
    total_distance_km: 45.7,
    total_time_hours: 3.5,
    total_cost_rub: 2850,
    model_used: 'qwen',
    fallback_reason: null,
    created_at: '2026-02-15T10:30:00Z'
  }

  const mockRouteWithFallback: Route = {
    ...mockRoute,
    model_used: 'llama',
    fallback_reason: 'Qwen unavailable, using fallback model'
  }

  const mockLocations = [
    {
      id: 'loc-1',
      name: 'Store A',
      address: 'г. Москва, ул. Тверская, д. 15',
      time_window_start: '09:00',
      time_window_end: '18:00'
    },
    {
      id: 'loc-2',
      name: 'Store B',
      address: 'г. Москва, ул. Арбат, д. 10',
      time_window_start: '10:00',
      time_window_end: '19:00'
    },
    {
      id: 'loc-3',
      name: 'Store C',
      address: 'г. Москва, ул. Новый Арбат, д. 24',
      time_window_start: '09:00',
      time_window_end: '20:00'
    }
  ]

  const mockOriginalMetrics = {
    total_distance_km: 60.2,
    total_time_hours: 4.8,
    total_cost_rub: 3500
  }

  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = mount(OptimizationResult, {
      props: {
        result: mockRoute,
        isLoading: false,
        error: null,
        originalMetrics: mockOriginalMetrics,
        locations: mockLocations
      }
    })
  })

  it('отображает заголовок с информацией о модели', () => {
    expect(wrapper.find('h3').text()).toBe('Результат оптимизации')
    expect(wrapper.text()).toContain(
      'Маршрут оптимизирован с использованием Qwen'
    )
    expect(wrapper.find('span.inline-flex').text()).toBe('Qwen')
  })

  it('отображает состояние загрузки', () => {
    const loadingWrapper = mount(OptimizationResult, {
      props: {
        result: null,
        isLoading: true,
        error: null,
        originalMetrics: null,
        locations: []
      }
    })

    expect(loadingWrapper.find('.animate-spin').exists()).toBe(true)
    expect(loadingWrapper.text()).toContain('Оптимизация маршрута...')
  })

  it('отображает состояние ошибки', () => {
    const errorMessage = 'Network error: Failed to optimize'
    const errorWrapper = mount(OptimizationResult, {
      props: {
        result: null,
        isLoading: false,
        error: errorMessage,
        originalMetrics: null,
        locations: []
      }
    })

    expect(errorWrapper.text()).toContain('Ошибка оптимизации')
    expect(errorWrapper.text()).toContain(errorMessage)
    expect(errorWrapper.find('button').text()).toBe('Попробовать снова')
  })

  it('эмитит событие retry при клике на кнопку повтора', async () => {
    const errorWrapper = mount(OptimizationResult, {
      props: {
        result: null,
        isLoading: false,
        error: 'Test error',
        originalMetrics: null,
        locations: []
      }
    })

    const retryButton = errorWrapper.find('button')
    await retryButton.trigger('click')

    expect(errorWrapper.emitted('retry')).toBeTruthy()
  })

  it('отображает ключевые метрики маршрута', () => {
    const metrics = wrapper.findAll('.bg-gray-50.rounded-lg.p-4')

    expect(metrics.length).toBe(3)
    expect(metrics[0].text()).toContain('45.7 км')
    expect(metrics[1].text()).toContain('3.5 ч')
    expect(metrics[2].text()).toContain('2850 ₽')
  })

  it('отображает исходные метрики для сравнения', () => {
    const metrics = wrapper.findAll('.bg-gray-50.rounded-lg.p-4')

    expect(metrics[0].text()).toContain('Было: 60.2 км')
    expect(metrics[1].text()).toContain('Было: 4.8 ч')
    expect(metrics[2].text()).toContain('Было: 3500 ₽')
  })

  it('отображает бейдж улучшения при положительной оптимизации', () => {
    const improvementBadge = wrapper.find('.bg-green-50')
    expect(improvementBadge.exists()).toBe(true)
    expect(improvementBadge.text()).toContain('Улучшение на')
  })

  it('не отображает бейдж улучшения при отсутствии исходных метрик', () => {
    const wrapperWithoutOriginal = mount(OptimizationResult, {
      props: {
        result: mockRoute,
        isLoading: false,
        error: null,
        originalMetrics: null,
        locations: mockLocations
      }
    })

    const improvementBadge = wrapperWithoutOriginal.find('.bg-green-50')
    expect(improvementBadge.exists()).toBe(false)
  })

  it('отображает причину использования резервной модели', () => {
    const wrapperWithFallback = mount(OptimizationResult, {
      props: {
        result: mockRouteWithFallback,
        isLoading: false,
        error: null,
        originalMetrics: mockOriginalMetrics,
        locations: mockLocations
      }
    })

    const fallbackReason = wrapperWithFallback.find('.bg-yellow-50')
    expect(fallbackReason.exists()).toBe(true)
    expect(fallbackReason.text()).toContain('Использована резервная модель')
    expect(fallbackReason.text()).toContain(
      'Qwen unavailable, using fallback model'
    )
  })

  it('отображает временные окна для каждой локации', () => {
    const timeWindows = wrapper.findAll('.text-sm.text-gray-500')
    // Последние 3 элемента - временные окна локаций
    const locationTimeWindows = timeWindows.slice(-3)

    expect(locationTimeWindows[0].text()).toBe('09:00 - 18:00')
    expect(locationTimeWindows[1].text()).toBe('10:00 - 19:00')
    expect(locationTimeWindows[2].text()).toBe('09:00 - 20:00')
  })

  it('отображает номера шагов для каждой локации', () => {
    const stepNumbers = wrapper.findAll('.bg-blue-100.rounded-full')
    expect(stepNumbers.length).toBe(3)
    expect(stepNumbers[0].text()).toBe('1')
    expect(stepNumbers[1].text()).toBe('2')
    expect(stepNumbers[2].text()).toBe('3')
  })

  it('эмитит событие reset при клике на кнопку сброса', async () => {
    const resetButton = wrapper
      .findAll('button')
      .find((b) => b.text().includes('Новая оптимизация'))
    expect(resetButton).toBeDefined()

    await resetButton!.trigger('click')
    expect(wrapper.emitted('reset')).toBeTruthy()
  })

  it('эмитит событие save при клике на кнопку сохранения', async () => {
    const saveButton = wrapper
      .findAll('button')
      .find((b) => b.text().includes('Сохранить маршрут'))
    expect(saveButton).toBeDefined()

    await saveButton!.trigger('click')
    expect(wrapper.emitted('save')).toBeTruthy()
  })

  it('корректно отображает название модели в бейдже', () => {
    const modelBadge = wrapper.find('span.inline-flex')
    expect(modelBadge.classes()).toContain('bg-purple-100')
    expect(modelBadge.classes()).toContain('text-purple-800')
  })

  it('корректно обрабатывает отсутствие локаций', () => {
    const wrapperWithoutLocations = mount(OptimizationResult, {
      props: {
        result: mockRoute,
        isLoading: false,
        error: null,
        originalMetrics: mockOriginalMetrics,
        locations: []
      }
    })

    const locationElements = wrapperWithoutLocations.findAll('.flex-1')
    expect(locationElements[0].text()).toContain('loc-1')
    expect(locationElements[1].text()).toContain('loc-2')
  })

  it('правильно вычисляет процент улучшения', async () => {
    const vm = wrapper.vm as any

    // Проверяем, что процент улучшения положительный
    expect(vm.improvementPercentageNumber).toBeGreaterThan(0)
    expect(vm.improvementPercentageString).toMatch(/^\d+\.\d$/)
  })

  it('не показывает бейдж улучшения при отрицательной оптимизации', () => {
    const worseMetrics = {
      total_distance_km: 30,
      total_time_hours: 2,
      total_cost_rub: 2000
    }

    const wrapperWithWorse = mount(OptimizationResult, {
      props: {
        result: {
          ...mockRoute,
          total_distance_km: 35,
          total_time_hours: 2.5,
          total_cost_rub: 2500
        },
        isLoading: false,
        error: null,
        originalMetrics: worseMetrics,
        locations: mockLocations
      }
    })

    const improvementBadge = wrapperWithWorse.find('.bg-green-50')
    expect(improvementBadge.exists()).toBe(false)
  })
})
