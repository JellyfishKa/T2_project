import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import ModelComparison from '@/components/dashboard/ModelComparison.vue'

describe('ModelComparison.vue', () => {
  // Мокаем данные в формате API (ApiBenchmarkResult)
  const mockApiResults = [
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
  ]

  const mockRecommendations = [
    {
      scenario: 'Быстрые запросы',
      recommended_model: 'qwen',
      reason: 'Бесплатно и очень быстро'
    }
  ]

  it('отображает skeleton loader при загрузке', () => {
    const wrapper = mount(ModelComparison, {
      props: {
        benchmarkResults: [],
        recommendations: [],
        isLoading: true
      },
      global: {
        stubs: {
          SkeletonLoader: {
            template: '<div class="skeleton-loader"></div>'
          }
        }
      }
    })

    expect(wrapper.findAll('.skeleton-loader').length).toBe(4)
  })

  it('отображает рекомендации', () => {
    const wrapper = mount(ModelComparison, {
      props: {
        benchmarkResults: mockApiResults,
        recommendations: mockRecommendations,
        isLoading: false
      },
      global: {
        stubs: {
          SkeletonLoader: true
        }
      }
    })

    expect(wrapper.text()).toContain('Рекомендации')
    expect(wrapper.text()).toContain('Быстрые запросы')
    expect(wrapper.text()).toContain('Qwen')
  })

  it('отображает пустое состояние', () => {
    const wrapper = mount(ModelComparison, {
      props: {
        benchmarkResults: [],
        recommendations: [],
        isLoading: false
      },
      global: {
        stubs: {
          SkeletonLoader: true
        }
      }
    })

    expect(wrapper.text()).toContain('Нет результатов бенчмарка')
  })

  it('корректно преобразует данные из API в формат отображения', () => {
    const wrapper = mount(ModelComparison, {
      props: {
        benchmarkResults: mockApiResults,
        recommendations: [],
        isLoading: false
      },
      global: {
        stubs: {
          SkeletonLoader: true
        }
      }
    })

    // Проверяем, что метод displayResults() работает правильно
    const vm = wrapper.vm as any
    const displayResults = vm.displayResults()

    expect(displayResults).toHaveLength(2)
    expect(displayResults[0]).toHaveProperty('model', 'llama')
    expect(displayResults[0]).toHaveProperty('num_tests', 100)
    expect(displayResults[0]).toHaveProperty('min_response_time_ms')
    expect(displayResults[0]).toHaveProperty('max_response_time_ms')
    expect(displayResults[0]).toHaveProperty('timestamp')
  })

  it('правильно обрабатывает пустой массив результатов', () => {
    const wrapper = mount(ModelComparison, {
      props: {
        benchmarkResults: [],
        recommendations: [],
        isLoading: false
      },
      global: {
        stubs: {
          SkeletonLoader: true
        }
      }
    })

    const vm = wrapper.vm as any
    const displayResults = vm.displayResults()
    expect(displayResults).toHaveLength(0)
  })

  it('правильно вычисляет ширину для времени ответа', () => {
    const wrapper = mount(ModelComparison, {
      props: {
        benchmarkResults: mockApiResults,
        recommendations: [],
        isLoading: false
      },
      global: {
        stubs: {
          SkeletonLoader: true
        }
      }
    })

    const vm = wrapper.vm as any

    // Время меньше 2000 мс
    expect(vm.getResponseTimeWidth(1000)).toBe(50)

    // Время больше 2000 мс (должно быть ограничено 100%)
    expect(vm.getResponseTimeWidth(2500)).toBe(100)
  })

  it('правильно вычисляет ширину для стоимости', () => {
    const wrapper = mount(ModelComparison, {
      props: {
        benchmarkResults: mockApiResults,
        recommendations: [],
        isLoading: false
      },
      global: {
        stubs: {
          SkeletonLoader: true
        }
      }
    })

    const vm = wrapper.vm as any

    // Стоимость меньше 300
    expect(vm.getCostWidth(150)).toBe(50)

    // Стоимость больше 300 (должна быть ограничена 100%)
    expect(vm.getCostWidth(400)).toBe(100)
  })

  it('правильно определяет цвет для времени ответа', () => {
    const wrapper = mount(ModelComparison, {
      props: {
        benchmarkResults: mockApiResults,
        recommendations: [],
        isLoading: false
      },
      global: {
        stubs: {
          SkeletonLoader: true
        }
      }
    })

    const vm = wrapper.vm as any

    expect(vm.getResponseTimeColor(500)).toBe('bg-green-500') // < 800
    expect(vm.getResponseTimeColor(1000)).toBe('bg-yellow-500') // 800-1500
    expect(vm.getResponseTimeColor(2000)).toBe('bg-red-500') // > 1500
  })

  it('правильно определяет цвет для успешности', () => {
    const wrapper = mount(ModelComparison, {
      props: {
        benchmarkResults: mockApiResults,
        recommendations: [],
        isLoading: false
      },
      global: {
        stubs: {
          SkeletonLoader: true
        }
      }
    })

    const vm = wrapper.vm as any

    expect(vm.getSuccessRateColor(0.99)).toBe('text-green-600') // >= 0.95
    expect(vm.getSuccessRateColor(0.9)).toBe('text-yellow-600') // 0.85-0.95
    expect(vm.getSuccessRateColor(0.8)).toBe('text-red-600') // < 0.85
  })
})
