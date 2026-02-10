import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import ConstraintsPanel from '@/components/optimize/ConstraintsPanel.vue'
import { nextTick } from 'vue'

describe('ConstraintsPanel.vue', () => {
  const defaultConstraints = {
    vehicleCapacity: 1,
    maxDistance: 500,
    startTime: '08:00',
    endTime: '20:00'
  }

  let wrapper: any

  beforeEach(() => {
    wrapper = mount(ConstraintsPanel, {
      props: {
        constraints: defaultConstraints
      }
    })
  })

  it('renders constraints panel with all controls', () => {
    // Проверяем заголовок
    expect(wrapper.find('h3').text()).toBe('Ограничения')
    
    // Проверяем наличие всех слайдеров
    expect(wrapper.find('input#vehicleCapacity').exists()).toBe(true)
    expect(wrapper.find('input#maxDistance').exists()).toBe(true)
    
    // Проверяем временные поля
    expect(wrapper.find('input#startTime').exists()).toBe(true)
    expect(wrapper.find('input#endTime').exists()).toBe(true)
    
    // Проверяем дополнительные поля
    expect(wrapper.find('input#maxStops').exists()).toBe(true)
    expect(wrapper.find('textarea#forbiddenRoads').exists()).toBe(true)
    
    // Проверяем кнопку сброса
    expect(wrapper.find('button').text()).toBe('Сбросить ограничения')
  })

  it('displays initial constraint values', () => {
    const vehicleCapacityValue = wrapper.find('span.text-gray-500').text()
    expect(vehicleCapacityValue).toBe('1 ед.')
    
    const maxDistanceValue = wrapper.findAll('span.text-gray-500')[1].text()
    expect(maxDistanceValue).toBe('500 км')
    
    const startTimeInput = wrapper.find('input#startTime')
    expect((startTimeInput.element as HTMLInputElement).value).toBe('08:00')
    
    const endTimeInput = wrapper.find('input#endTime')
    expect((endTimeInput.element as HTMLInputElement).value).toBe('20:00')
  })

  it('emits update-constraints when vehicle capacity changes', async () => {
    const vehicleCapacityInput = wrapper.find('input#vehicleCapacity')
    
    // Меняем значение слайдера
    await vehicleCapacityInput.setValue(3)
    await nextTick()
    
    expect(wrapper.emitted('update-constraints')).toBeTruthy()
    if (wrapper.emitted('update-constraints')) {
      const updateEvent = wrapper.emitted('update-constraints')![0][0]
      expect(updateEvent.vehicleCapacity).toBe(3)
    }
  })

  it('emits update-constraints when max distance changes', async () => {
    const maxDistanceInput = wrapper.find('input#maxDistance')
    
    // Меняем значение слайдера
    await maxDistanceInput.setValue(750)
    await nextTick()
    
    expect(wrapper.emitted('update-constraints')).toBeTruthy()
    if (wrapper.emitted('update-constraints')) {
      const updateEvent = wrapper.emitted('update-constraints')![0][0]
      expect(updateEvent.maxDistance).toBe(750)
    }
  })

  it('emits update-constraints when time changes', async () => {
    const startTimeInput = wrapper.find('input#startTime')
    
    // Меняем время начала
    await startTimeInput.setValue('09:00')
    await nextTick()
    
    expect(wrapper.emitted('update-constraints')).toBeTruthy()
    if (wrapper.emitted('update-constraints')) {
      const updateEvent = wrapper.emitted('update-constraints')![0][0]
      expect(updateEvent.startTime).toBe('09:00')
    }
  })

  it('emits update-constraints when max stops changes', async () => {
    const maxStopsInput = wrapper.find('input#maxStops')
    
    // Устанавливаем максимальное количество остановок
    await maxStopsInput.setValue(10)
    await nextTick()
    
    expect(wrapper.emitted('update-constraints')).toBeTruthy()
    if (wrapper.emitted('update-constraints')) {
      const updateEvent = wrapper.emitted('update-constraints')![0][0]
      expect(updateEvent.maxStops).toBe(10)
    }
  })

  it('handles forbidden roads input', async () => {
    const forbiddenRoadsInput = wrapper.find('textarea#forbiddenRoads')
    
    // Вводим запрещенные дороги
    await forbiddenRoadsInput.setValue('МКАД, ТТК, Садовое кольцо')
    await nextTick()
    
    expect(wrapper.emitted('update-constraints')).toBeTruthy()
    if (wrapper.emitted('update-constraints')) {
      const updateEvent = wrapper.emitted('update-constraints')!.slice(-1)[0][0]
      expect(updateEvent.forbiddenRoads).toEqual(['МКАД', 'ТТК', 'Садовое кольцо'])
    }
  })

  it('removes individual forbidden roads', async () => {
    // Сначала добавляем несколько дорог
    wrapper = mount(ConstraintsPanel, {
      props: {
        constraints: {
          ...defaultConstraints,
          forbiddenRoads: ['МКАД', 'ТТК', 'Садовое кольцо']
        }
      }
    })
    
    await nextTick()
    
    // Находим и кликаем на кнопку удаления первой дороги
    const removeButtons = wrapper.findAll('button.text-red-600')
    expect(removeButtons.length).toBe(3) // По кнопке на каждую дорогу
    
    await removeButtons[0].trigger('click')
    await nextTick()
    
    expect(wrapper.emitted('update-constraints')).toBeTruthy()
    if (wrapper.emitted('update-constraints')) {
      const updateEvent = wrapper.emitted('update-constraints')!.slice(-1)[0][0]
      expect(updateEvent.forbiddenRoads).toEqual(['ТТК', 'Садовое кольцо'])
    }
  })

  it('resets constraints to defaults when reset button is clicked', async () => {
    const resetButton = wrapper.find('button')
    await resetButton.trigger('click')
    
    expect(wrapper.emitted('update-constraints')).toBeTruthy()
    if (wrapper.emitted('update-constraints')) {
      const updateEvent = wrapper.emitted('update-constraints')!.slice(-1)[0][0]
      
      expect(updateEvent.vehicleCapacity).toBe(1)
      expect(updateEvent.maxDistance).toBe(500)
      expect(updateEvent.startTime).toBe('08:00')
      expect(updateEvent.endTime).toBe('20:00')
      expect(updateEvent.maxStops).toBeUndefined()
      expect(updateEvent.forbiddenRoads).toEqual([])
    }
  })

  it('updates local state when props change', async () => {
    await wrapper.setProps({
      constraints: {
        vehicleCapacity: 3,
        maxDistance: 750,
        startTime: '10:00',
        endTime: '22:00',
        maxStops: 5,
        forbiddenRoads: ['Новая дорога']
      }
    })
    
    await nextTick()
    
    // Проверяем, что значения обновились
    const vehicleCapacityValue = wrapper.find('span.text-gray-500').text()
    expect(vehicleCapacityValue).toBe('3 ед.')
    
    const maxDistanceValue = wrapper.findAll('span.text-gray-500')[1].text()
    expect(maxDistanceValue).toBe('750 км')
    
    const startTimeInput = wrapper.find('input#startTime')
    expect((startTimeInput.element as HTMLInputElement).value).toBe('10:00')
    
    const forbiddenRoadsInput = wrapper.find('textarea#forbiddenRoads')
    expect((forbiddenRoadsInput.element as HTMLTextAreaElement).value).toBe('Новая дорога')
  })

  it('has correct range limits for vehicle capacity', () => {
    const vehicleCapacityInput = wrapper.find('input#vehicleCapacity')
    expect(vehicleCapacityInput.attributes('min')).toBe('1')
    expect(vehicleCapacityInput.attributes('max')).toBe('4')
    expect(vehicleCapacityInput.attributes('step')).toBe('1')
  })

  it('has correct range limits for max distance', () => {
    const maxDistanceInput = wrapper.find('input#maxDistance')
    expect(maxDistanceInput.attributes('min')).toBe('50')
    expect(maxDistanceInput.attributes('max')).toBe('1000')
    expect(maxDistanceInput.attributes('step')).toBe('50')
  })

  it('shows forbidden roads as tags', () => {
    wrapper = mount(ConstraintsPanel, {
      props: {
        constraints: {
          ...defaultConstraints,
          forbiddenRoads: ['МКАД', 'ТТК']
        }
      }
    })
    
    const tags = wrapper.findAll('span.bg-red-100')
    expect(tags.length).toBe(2)
    expect(tags[0].text()).toContain('МКАД')
    expect(tags[1].text()).toContain('ТТК')
  })
})