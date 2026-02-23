import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import HealthStatus from '@/components/dashboard/HealthStatus.vue'
import type { HealthStatus as HealthStatusType } from '@/services/api'

describe('HealthStatus.vue', () => {
  const healthyStatus: HealthStatusType = {
    status: 'healthy',
    services: {
      database: 'connected',
      llama: 'connected',
      qwen: 'available'
    }
  }

  const unhealthyStatus: HealthStatusType = {
    status: 'unhealthy',
    services: {
      database: 'disconnected',
      llama: 'error',
      qwen: 'unavailable'
    }
  }

  it('отображает здоровый статус', () => {
    const wrapper = mount(HealthStatus, {
      props: { status: healthyStatus }
    })

    expect(wrapper.text()).toContain('Система работает нормально')
    expect(wrapper.text()).toContain('Все системы работают')
    expect(wrapper.find('.bg-green-500').exists()).toBe(true)
    expect(wrapper.find('.text-green-600').exists()).toBe(true)
  })

  it('отображает нездоровый статус', () => {
    const wrapper = mount(HealthStatus, {
      props: { status: unhealthyStatus }
    })

    expect(wrapper.text()).toContain('Обнаружены проблемы')
    expect(wrapper.text()).toContain('Есть проблемы')
    expect(wrapper.find('.bg-red-500').exists()).toBe(true)
    expect(wrapper.find('.text-red-600').exists()).toBe(true)
  })

  it('отображает статусы всех сервисов', () => {
    const wrapper = mount(HealthStatus, {
      props: { status: healthyStatus }
    })

    expect(wrapper.text()).toContain('database')
    expect(wrapper.text()).toContain('llama')
    expect(wrapper.text()).toContain('qwen')
    expect(wrapper.text()).toContain('Подключено')
    expect(wrapper.text()).toContain('Доступно')
  })

  it('правильно определяет цвета статусов сервисов', () => {
    const wrapper = mount(HealthStatus, {
      props: { status: healthyStatus }
    })

    const dots = wrapper.findAll('.h-2.w-2.rounded-full')

    // database: connected -> green
    expect(dots[0].classes()).toContain('bg-green-500')
    // llama: connected -> green
    expect(dots[1].classes()).toContain('bg-green-500')
    // qwen: available -> blue
    expect(dots[2].classes()).toContain('bg-blue-500')
  })

  it('правильно определяет цвета границы', () => {
    const healthyWrapper = mount(HealthStatus, {
      props: { status: healthyStatus }
    })
    expect(healthyWrapper.find('.border-green-200').exists()).toBe(true)

    const unhealthyWrapper = mount(HealthStatus, {
      props: { status: unhealthyStatus }
    })
    expect(unhealthyWrapper.find('.border-red-200').exists()).toBe(true)
  })

  it('правильно переводит статусы сервисов', () => {
    const wrapper = mount(HealthStatus, {
      props: { status: healthyStatus }
    })

    const serviceTexts = wrapper.findAll('.text-xs.text-gray-500')
    expect(serviceTexts[0].text()).toBe('Подключено')
    expect(serviceTexts[1].text()).toBe('Подключено')
    expect(serviceTexts[2].text()).toBe('Доступно')
  })

  it('отображает правильные иконки', () => {
    const healthyWrapper = mount(HealthStatus, {
      props: { status: healthyStatus }
    })
    expect(healthyWrapper.find('path[d*="M9 12l2 2 4-4m6 2a9"]').exists()).toBe(
      true
    )

    const unhealthyWrapper = mount(HealthStatus, {
      props: { status: unhealthyStatus }
    })
    expect(
      unhealthyWrapper.find('path[d*="M12 9v2m0 4h.01m-6.938"]').exists()
    ).toBe(true)
  })
})
