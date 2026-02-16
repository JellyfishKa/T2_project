import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import RouteList from '@/components/dashboard/RouteList.vue'

describe('RouteList.vue', () => {
  const mockRoutes = [
    {
      id: 'route-1',
      name: 'Test Route 1',
      locations: ['store-1', 'store-2'],
      total_distance_km: 10.5,
      total_time_hours: 1.5,
      total_cost_rub: 1250,
      model_used: 'llama',
      fallback_reason: null,
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
      created_at: '2026-02-12T14:30:00Z'
    }
  ]

  it('TC-RL-001: отображает skeleton loader при загрузке', () => {
    const wrapper = mount(RouteList, {
      props: {
        routes: [],
        isLoading: true
      },
      global: {
        stubs: {
          SkeletonLoader: true
        }
      }
    })

    expect(wrapper.findAllComponents({ name: 'SkeletonLoader' }).length).toBe(5)
  })

  it('TC-RL-002: отображает список маршрутов', () => {
    const wrapper = mount(RouteList, {
      props: {
        routes: mockRoutes,
        isLoading: false
      }
    })

    expect(wrapper.text()).toContain('Test Route 1')
    expect(wrapper.text()).toContain('Test Route 2')
    expect(wrapper.findAll('tr').length).toBe(3) // header + 2 rows
  })

  it('TC-RL-003: отображает пустое состояние', () => {
    const wrapper = mount(RouteList, {
      props: {
        routes: [],
        isLoading: false
      }
    })

    expect(wrapper.text()).toContain('Нет маршрутов')
  })

  it('TC-RL-004: эмитит событие select-route при клике на маршрут', async () => {
    const wrapper = mount(RouteList, {
      props: {
        routes: mockRoutes,
        isLoading: false
      }
    })

    const firstRow = wrapper.find('tbody tr')
    await firstRow.trigger('click')

    expect(wrapper.emitted('select-route')).toBeTruthy()
    expect(wrapper.emitted('select-route')![0][0]).toBe('route-1')
  })

  it('TC-RL-005: подсвечивает выбранный маршрут', () => {
    const wrapper = mount(RouteList, {
      props: {
        routes: mockRoutes,
        selectedRouteId: 'route-1',
        isLoading: false
      }
    })

    const rows = wrapper.findAll('tbody tr')
    expect(rows[0].classes()).toContain('bg-blue-50')
    expect(rows[1].classes()).not.toContain('bg-blue-50')
  })

  it('TC-RL-006: поддерживает сортировку', async () => {
    const wrapper = mount(RouteList, {
      props: {
        routes: mockRoutes,
        sortable: true,
        isLoading: false
      }
    })

    const headers = wrapper.findAll('th')
    const distanceHeader = headers[2] // Заголовок "Расстояние"

    await distanceHeader.trigger('click')

    expect(wrapper.emitted('sort')).toBeTruthy()
    expect(wrapper.emitted('sort')![0][0]).toBe('total_distance_km')
    expect(wrapper.emitted('sort')![0][1]).toBe('asc')
  })
})
