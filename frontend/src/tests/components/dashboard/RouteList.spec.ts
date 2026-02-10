import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import RouteList from '@/components/dashboard/RouteList.vue'
import type { Route } from '@/services/api'

describe('RouteList.vue', () => {
  const mockRoutes: Route[] = [
    {
      id: 'route-1',
      name: 'Центральный маршрут',
      locations: ['store-1', 'store-2'],
      total_distance_km: 28.5,
      total_time_hours: 3.2,
      total_cost_rub: 1850,
      model_used: 'llama',
      created_at: '2024-01-06T09:15:00Z'
    },
    {
      id: 'route-2',
      name: 'Северо-Западный маршрут',
      locations: ['store-3', 'store-1'],
      total_distance_km: 35.7,
      total_time_hours: 4.1,
      total_cost_rub: 2100,
      model_used: 'qwen',
      created_at: '2024-01-05T14:30:00Z'
    }
  ]

  it('отображает список маршрутов', () => {
    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes }
    })

    expect(wrapper.text()).toContain('Центральный маршрут')
    expect(wrapper.text()).toContain('Северо-Западный маршрут')
    expect(wrapper.text()).toContain('28.5 км')
    expect(wrapper.text()).toContain('3.2 ч')
    expect(wrapper.text()).toContain('1850 ₽')
  })

  it('эмитирует событие при выборе маршрута', async () => {
    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes }
    })

    // Находим первую строку таблицы и кликаем
    const firstRow = wrapper.findAll('tr.cursor-pointer')[0]
    await firstRow.trigger('click')

    // Проверяем, что событие было эмитировано с правильным ID
    expect(wrapper.emitted('select-route')).toBeTruthy()
    expect(wrapper.emitted('select-route')?.[0]).toEqual(['route-1'])
  })

  it('подсвечивает выбранный маршрут', () => {
    const wrapper = mount(RouteList, {
      props: { 
        routes: mockRoutes,
        selectedRouteId: 'route-2' 
      }
    })

    // Находим строку выбранного маршрута
    const selectedRow = wrapper.find('tr.bg-blue-50')
    expect(selectedRow.exists()).toBe(true)
    expect(selectedRow.text()).toContain('Северо-Западный маршрут')
  })

  it('отображает пустое состояние', () => {
    const wrapper = mount(RouteList, {
      props: { routes: [] }
    })

    expect(wrapper.text()).toContain('Нет маршрутов')
    expect(wrapper.text()).toContain('Создайте первый маршрут в разделе Optimize')
  })


  it('отображает мобильные карточки на маленьких экранах', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375
    })

    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes },
      global: {
        mocks: {
          $screen: { sm: false }
        }
      }
    })

    expect(wrapper.find('.sm\\:hidden').exists()).toBe(true)
    expect(wrapper.text()).toContain('Расстояние')
    expect(wrapper.text()).toContain('Время')
    expect(wrapper.text()).toContain('Стоимость')
  })

  it('правильно отображает иконки моделей', () => {
    const wrapper = mount(RouteList, {
      props: { 
        routes: [
          {
            id: 'route-1',
            name: 'Llama Route',
            locations: ['store-1'],
            total_distance_km: 10,
            total_time_hours: 1,
            total_cost_rub: 100,
            model_used: 'llama',
            created_at: '2024-01-06T09:15:00Z'
          },
          {
            id: 'route-2',
            name: 'Qwen Route',
            locations: ['store-2'],
            total_distance_km: 20,
            total_time_hours: 2,
            total_cost_rub: 200,
            model_used: 'qwen',
            created_at: '2024-01-06T09:15:00Z'
          }
        ]
      }
    })

    // Проверяем инициалы
    const icons = wrapper.findAll('.font-bold.text-sm')
    expect(icons[0].text()).toBe('L')
    expect(icons[1].text()).toBe('Q')

    // Проверяем цвета
    const llamaIcon = wrapper.find('.bg-blue-500')
    const qwenIcon = wrapper.find('.bg-purple-500')
    expect(llamaIcon.exists()).toBe(true)
    expect(qwenIcon.exists()).toBe(true)
  })
})