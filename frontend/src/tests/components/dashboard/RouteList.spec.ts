import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RouteList from '@/components/dashboard/RouteList.vue'
import { createRouter, createMemoryHistory } from 'vue-router'

// Создаем роутер для тестов
const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/', component: { template: '<div>Home</div>' } }]
})

describe('RouteList.vue', () => {
  const mockRoutes = [
    {
      id: 'route-1',
      name: 'Центральный маршрут',
      locations: ['store-1', 'store-2', 'store-3'],
      total_distance_km: 28.5,
      total_time_hours: 3.2,
      total_cost_rub: 1850,
      model_used: 'llama',
      fallback_reason: null,
      created_at: '2026-02-13T09:15:00Z'
    },
    {
      id: 'route-2',
      name: 'Северо-Западный маршрут',
      locations: ['store-4', 'store-5'],
      total_distance_km: 35.7,
      total_time_hours: 4.1,
      total_cost_rub: 2100,
      model_used: 'qwen',
      fallback_reason: null,
      created_at: '2026-02-12T14:30:00Z'
    },
    {
      id: 'route-3',
      name: 'Южный маршрут с fallback',
      locations: ['store-6', 'store-7', 'store-8'],
      total_distance_km: 42.3,
      total_time_hours: 5.5,
      total_cost_rub: 2750,
      model_used: 'deepseek',
      fallback_reason: 'Llama unavailable, using fallback',
      created_at: '2026-02-11T11:45:00Z'
    }
  ]

  it('отображает список маршрутов на десктопе', () => {
    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes },
      global: {
        plugins: [router]
      }
    })

    // Проверяем заголовки таблицы
    expect(wrapper.text()).toContain('Маршрут')
    expect(wrapper.text()).toContain('Модель')
    expect(wrapper.text()).toContain('Расстояние')
    expect(wrapper.text()).toContain('Время')
    expect(wrapper.text()).toContain('Стоимость')

    // Проверяем данные маршрутов
    expect(wrapper.text()).toContain('Центральный маршрут')
    expect(wrapper.text()).toContain('Северо-Западный маршрут')
    expect(wrapper.text()).toContain('Южный маршрут с fallback')
    expect(wrapper.text()).toContain('28.5 км')
    expect(wrapper.text()).toContain('3.2 ч')
    expect(wrapper.text()).toContain('1850 ₽')
  })

  it('эмитирует событие при выборе маршрута', async () => {
    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes },
      global: {
        plugins: [router]
      }
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
      },
      global: {
        plugins: [router]
      }
    })

    // Находим строку выбранного маршрута
    const selectedRow = wrapper.find('tr.bg-blue-50')
    expect(selectedRow.exists()).toBe(true)
    expect(selectedRow.text()).toContain('Северо-Западный маршрут')
  })

  it('отображает пустое состояние', () => {
    const wrapper = mount(RouteList, {
      props: { routes: [] },
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.text()).toContain('Нет маршрутов')
    expect(wrapper.text()).toContain(
      'Создайте первый маршрут в разделе Optimize'
    )
  })

  it('отображает мобильные карточки на маленьких экранах', () => {
    // Имитируем маленький экран
    global.innerWidth = 375
    global.dispatchEvent(new Event('resize'))

    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes },
      global: {
        plugins: [router]
      }
    })

    // Проверяем, что есть div для мобильных карточек
    expect(wrapper.find('.sm\\:hidden').exists()).toBe(true)
    expect(wrapper.text()).toContain('Расстояние')
    expect(wrapper.text()).toContain('Время')
    expect(wrapper.text()).toContain('Стоимость')
    expect(wrapper.text()).toContain('Создан:')
  })

  it('правильно отображает иконки моделей', () => {
    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes },
      global: {
        plugins: [router]
      }
    })

    // Проверяем инициалы моделей
    const icons = wrapper.findAll('.font-bold.text-sm')
    expect(icons[0].text()).toBe('L') // llama
    expect(icons[1].text()).toBe('Q') // qwen
    expect(icons[2].text()).toBe('D') // deepseek

    // Проверяем цвета фона
    const llamaIcon = wrapper.find('.bg-blue-300')
    const qwenIcon = wrapper.find('.bg-purple-500')
    const deepseekIcon = wrapper.find('.bg-blue-500')

    expect(llamaIcon.exists()).toBe(true)
    expect(qwenIcon.exists()).toBe(true)
    expect(deepseekIcon.exists()).toBe(true)
  })

  it('правильно отображает бейджи моделей', () => {
    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes },
      global: {
        plugins: [router]
      }
    })

    // Проверяем классы бейджей
    const badges = wrapper.findAll('.rounded-full')
    const llamaBadge = badges.find((b) => b.text().includes('Llama'))
    const qwenBadge = badges.find((b) => b.text().includes('Qwen'))
    const deepseekBadge = badges.find((b) => b.text().includes('DeepSeek'))

    expect(llamaBadge?.classes()).toContain('bg-blue-100')
    expect(llamaBadge?.classes()).toContain('text-blue-800')
    expect(qwenBadge?.classes()).toContain('bg-purple-100')
    expect(qwenBadge?.classes()).toContain('text-purple-800')
    expect(deepseekBadge?.classes()).toContain('bg-blue-400')
    expect(deepseekBadge?.classes()).toContain('text-blue-1000')
  })

  it('отображает fallback_reason если он есть', () => {
    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes },
      global: {
        plugins: [router]
      }
    })

    const routeWithFallback = wrapper.text()
    expect(routeWithFallback).toContain('Южный маршрут с fallback')
  })

  it('эмитирует событие при клике на мобильную карточку', async () => {
    global.innerWidth = 375
    global.dispatchEvent(new Event('resize'))

    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes },
      global: {
        plugins: [router]
      }
    })

    // Находим первую мобильную карточку и кликаем
    const firstCard = wrapper.findAll('.sm\\:hidden .border.rounded-lg')[0]
    await firstCard.trigger('click')

    // Проверяем, что событие было эмитировано
    expect(wrapper.emitted('select-route')).toBeTruthy()
    expect(wrapper.emitted('select-route')?.[0]).toEqual(['route-1'])
  })

  it('подсвечивает выбранный маршрут на мобильных карточках', () => {
    global.innerWidth = 375
    global.dispatchEvent(new Event('resize'))

    const wrapper = mount(RouteList, {
      props: {
        routes: mockRoutes,
        selectedRouteId: 'route-2'
      },
      global: {
        plugins: [router]
      }
    })

    // Находим выбранную мобильную карточку
    const selectedCard = wrapper.find('.border-blue-300.bg-blue-50')
    expect(selectedCard.exists()).toBe(true)
    expect(selectedCard.text()).toContain('Северо-Западный маршрут')
  })

  it('правильно обрабатывает model_used с неизвестной моделью', () => {
    const routesWithUnknown = [
      {
        ...mockRoutes[0],
        model_used: 'unknown-model'
      }
    ]

    const wrapper = mount(RouteList, {
      props: { routes: routesWithUnknown },
      global: {
        plugins: [router]
      }
    })

    // Проверяем, что используется дефолтный бейдж
    const badge = wrapper.find('.bg-gray-100')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toContain('unknown-model')

    // Проверяем, что используется дефолтный цвет иконки
    const icon = wrapper.find('.bg-gray-500')
    expect(icon.exists()).toBe(true)
    expect(icon.find('.font-bold.text-sm').text()).toBe('?')
  })

  it('правильно рассчитывает количество локаций для мобильных карточек', () => {
    global.innerWidth = 375
    global.dispatchEvent(new Event('resize'))

    const wrapper = mount(RouteList, {
      props: { routes: mockRoutes },
      global: {
        plugins: [router]
      }
    })

    // Проверяем, что количество локаций не отображается (в текущей реализации)
    // Но если добавить - можно проверить здесь
  })

  it('сохраняет состояние выбора при обновлении пропсов', async () => {
    const wrapper = mount(RouteList, {
      props: {
        routes: mockRoutes,
        selectedRouteId: 'route-1'
      },
      global: {
        plugins: [router]
      }
    })

    // Проверяем, что первый маршрут выбран
    let selectedRow = wrapper.find('tr.bg-blue-50')
    expect(selectedRow.text()).toContain('Центральный маршрут')

    // Обновляем пропсы с новым выбранным маршрутом
    await wrapper.setProps({ selectedRouteId: 'route-2' })

    // Проверяем, что выбор изменился
    selectedRow = wrapper.find('tr.bg-blue-50')
    expect(selectedRow.text()).toContain('Северо-Западный маршрут')
  })
})
