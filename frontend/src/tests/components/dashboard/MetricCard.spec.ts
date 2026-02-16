import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MetricCard from '@/components/dashboard/MetricCard.vue'

describe('MetricCard.vue', () => {
  it('отображает заголовок и значение', () => {
    const wrapper = mount(MetricCard, {
      props: {
        title: 'Общее расстояние',
        value: 125.5,
        unit: 'км',
        color: 'blue'
      }
    })

    expect(wrapper.text()).toContain('Общее расстояние')
    expect(wrapper.text()).toContain('125.5')
    expect(wrapper.text()).toContain('км')
  })

  it('форматирует целые числа без десятичных', () => {
    const wrapper = mount(MetricCard, {
      props: {
        title: 'Количество',
        value: 42,
        unit: 'шт',
        color: 'green'
      }
    })

    expect(wrapper.text()).toContain('42')
    expect(wrapper.text()).not.toContain('.0')
  })

  it('форматирует дробные числа с одним десятичным знаком', () => {
    const wrapper = mount(MetricCard, {
      props: {
        title: 'Процент',
        value: 98.765,
        unit: '%',
        color: 'red'
      }
    })

    expect(wrapper.text()).toContain('98.8')
  })

  it('рендерит без ошибок при минимальных пропсах', () => {
    expect(() => {
      mount(MetricCard, {
        props: {
          title: 'Тест',
          value: 0,
          unit: '',
          color: 'blue'
        }
      })
    }).not.toThrow()
  })
})
