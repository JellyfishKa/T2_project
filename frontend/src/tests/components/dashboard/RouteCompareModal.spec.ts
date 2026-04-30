import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('@/components/RouteMap.vue', () => ({
  default: {
    name: 'RouteMap',
    template: '<div data-testid="route-map"></div>',
    props: ['routes', 'points', 'height'],
  },
}))

import RouteCompareModal from '@/components/dashboard/RouteCompareModal.vue'

describe('RouteCompareModal.vue', () => {
  const comparison = {
    route_id: 'route-1',
    original: [
      {
        id: 'loc-1',
        name: 'Store 1',
        lat: 55.7558,
        lon: 37.6173,
        order: 1,
        address: 'Address 1',
        category: 'A',
      },
      {
        id: 'loc-2',
        name: 'Store 2',
        lat: 55.7489,
        lon: 37.616,
        order: 2,
        address: 'Address 2',
        category: 'B',
      },
    ],
    current: [
      {
        id: 'loc-2',
        name: 'Store 2',
        lat: 55.7489,
        lon: 37.616,
        order: 1,
        address: 'Address 2',
        category: 'B',
      },
      {
        id: 'loc-1',
        name: 'Store 1',
        lat: 55.7558,
        lon: 37.6173,
        order: 2,
        address: 'Address 1',
        category: 'A',
      },
    ],
    diff: {
      distance_delta_km: -3.5,
      time_delta_hours: -0.4,
      cost_delta_rub: -180,
      changed_stops_count: 2,
      improvement_percentage: 16.3,
    },
    model_used: 'qwen',
    created_at: '2026-04-22T11:15:00Z',
  }

  it('renders summary cards and passes two route sets into RouteMap', () => {
    const wrapper = mount(RouteCompareModal, {
      props: {
        open: true,
        comparison,
        routeName: 'Test Route',
      },
    })

    expect(wrapper.text()).toContain('Сравнение маршрута')
    expect(wrapper.text()).toContain('Δ км')
    expect(wrapper.text()).toContain('−3.5 км')
    expect(wrapper.text()).toContain('Изменено точек')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('↑1')
    expect(wrapper.text()).toContain('↓1')

    const routeMap = wrapper.findComponent({ name: 'RouteMap' })
    expect(routeMap.exists()).toBe(true)
    expect(routeMap.props('routes')).toHaveLength(2)
    expect(routeMap.props('routes')[0].id).toBe('original')
    expect(routeMap.props('routes')[1].selected).toBe(true)
  })

  it('emits close when close button is clicked', async () => {
    const wrapper = mount(RouteCompareModal, {
      props: {
        open: true,
        comparison,
        routeName: 'Test Route',
      },
    })

    await wrapper.find('button').trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
