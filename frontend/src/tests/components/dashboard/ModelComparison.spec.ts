import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ModelComparison from '@/components/dashboard/ModelComparison.vue'
import type { BenchmarkResult } from '@/services/api'

describe('ModelComparison.vue', () => {
  const mockBenchmarkResults: BenchmarkResult[] = [
    {
      model: 'llama',
      num_tests: 10,
      avg_response_time_ms: 1250,
      min_response_time_ms: 850,
      max_response_time_ms: 2100,
      avg_quality_score: 0.87,
      total_cost_rub: 250.0,
      success_rate: 1.0,
      timestamp: '2024-01-06T11:00:00Z'
    },
    {
      model: 'qwen',
      num_tests: 10,
      avg_response_time_ms: 450,
      min_response_time_ms: 350,
      max_response_time_ms: 650,
      avg_quality_score: 0.82,
      total_cost_rub: 0.0,
      success_rate: 1.0,
      timestamp: '2024-01-06T11:00:00Z'
    }
  ]

  it('отображает загрузочное состояние', () => {
    const wrapper = mount(ModelComparison, {
      props: { 
        benchmarkResults: [],
        isLoading: true 
      }
    })

    expect(wrapper.text()).toContain('Загрузка результатов бенчмарка...')
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
  })


  it('отображает пустое состояние', () => {
    const wrapper = mount(ModelComparison, {
      props: { 
        benchmarkResults: [],
        isLoading: false 
      }
    })

    expect(wrapper.text()).toContain('Нет результатов бенчмарка')
    expect(wrapper.text()).toContain('Запустите бенчмарк для сравнения моделей')
  })



  it('правильно определяет цвета для успешности', () => {
    const wrapper = mount(ModelComparison, {
      props: { 
        benchmarkResults: [
          {
            model: 'llama',
            num_tests: 10,
            avg_response_time_ms: 1000,
            min_response_time_ms: 800,
            max_response_time_ms: 1200,
            avg_quality_score: 0.9,
            total_cost_rub: 200,
            success_rate: 0.96, // зеленый
            timestamp: '2024-01-06T11:00:00Z'
          },
          {
            model: 'qwen',
            num_tests: 10,
            avg_response_time_ms: 500,
            min_response_time_ms: 400,
            max_response_time_ms: 600,
            avg_quality_score: 0.85,
            total_cost_rub: 0,
            success_rate: 0.86, // желтый
            timestamp: '2024-01-06T11:00:00Z'
          },
          {
            model: 'tpro',
            num_tests: 10,
            avg_response_time_ms: 1500,
            min_response_time_ms: 1200,
            max_response_time_ms: 1800,
            avg_quality_score: 0.95,
            total_cost_rub: 180,
            success_rate: 0.7, // красный
            timestamp: '2024-01-06T11:00:00Z'
          }
        ],
        isLoading: false 
      }
    })

    const successRates = wrapper.findAll('.font-semibold')
    expect(successRates[0].classes()).toContain('text-green-600')
    expect(successRates[1].classes()).toContain('text-yellow-600')
    expect(successRates[2].classes()).toContain('text-red-600')
  })
})