import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import LocationInput from '@/components/optimize/LocationInput.vue'
import { nextTick } from 'vue'

describe('LocationInput.vue', () => {
  const mockLocation = {
    id: 'test-location-1',
    name: 'Тестовый магазин',
    city: 'Москва',
    street: 'Тверская',
    houseNumber: '15',
    latitude: 55.7558,
    longitude: 37.6173,
    timeWindowStart: '09:00',
    timeWindowEnd: '18:00',
    priority: 'medium' as const
  }

  let wrapper: any

  beforeEach(() => {
    wrapper = mount(LocationInput, {
      props: {
        location: mockLocation,
        index: 0
      }
    })
  })

  it('renders location input with correct structure', () => {
    // Проверяем заголовок
    expect(wrapper.find('h4').text()).toBe('Магазин 1')
    
    // Проверяем наличие всех полей
    expect(wrapper.find('input[placeholder*="магазин"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="Москва"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder*="Тверская"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="15"]').exists()).toBe(true)
    
    // Проверяем координаты
    expect(wrapper.find('input[placeholder="55.7558"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="37.6173"]').exists()).toBe(true)
    
    // Проверяем временные окна
    expect(wrapper.find('input[type="time"]').exists()).toBe(true)
    
    // Проверяем приоритеты
    expect(wrapper.text()).toContain('Низкий')
    expect(wrapper.text()).toContain('Средний')
    expect(wrapper.text()).toContain('Высокий')
  })

  it('displays correct location data', () => {
    // Проверяем, что данные отображаются корректно
    const nameInput = wrapper.find('input[placeholder*="магазин"]')
    expect((nameInput.element as HTMLInputElement).value).toBe('Тестовый магазин')
    
    const cityInput = wrapper.find('input[placeholder="Москва"]')
    expect((cityInput.element as HTMLInputElement).value).toBe('Москва')
    
    const streetInput = wrapper.find('input[placeholder*="Тверская"]')
    expect((streetInput.element as HTMLInputElement).value).toBe('Тверская')
  })

  it('formats city name with capital letter', async () => {
    const cityInput = wrapper.find('input[placeholder="Москва"]')
    
    // Вводим город с маленькой буквы
    await cityInput.setValue('москва')
    await wrapper.vm.updateLocation()
    await nextTick()
    
    expect((cityInput.element as HTMLInputElement).value).toBe('Москва')
  })

  it('emits update event when input changes', async () => {
    const nameInput = wrapper.find('input[placeholder*="магазин"]')
    
    await nameInput.setValue('Новое название')
    await nextTick()
    
    expect(wrapper.emitted('update')).toBeTruthy()
    if (wrapper.emitted('update')) {
      const updateEvent = wrapper.emitted('update')![0][0]
      expect(updateEvent).toHaveProperty('name')
      expect(updateEvent.name).toBe('Новое название')
    }
  })

  

  it('disables delete button for first location', () => {
    wrapper = mount(LocationInput, {
      props: {
        location: mockLocation,
        index: 0 // Первая локация
      }
    })
    
    const deleteButton = wrapper.find('button.text-gray-400')
    expect(deleteButton.attributes('disabled')).toBe('')
    expect(deleteButton.classes()).toContain('opacity-50')
    expect(deleteButton.classes()).toContain('cursor-not-allowed')
  })

  it('enables delete button for non-first location', () => {
    wrapper = mount(LocationInput, {
      props: {
        location: mockLocation,
        index: 1 // Не первая локация
      }
    })
    
    const deleteButton = wrapper.find('button.text-gray-400')
    expect(deleteButton.attributes('disabled')).toBeUndefined()
    expect(deleteButton.classes()).not.toContain('opacity-50')
    expect(deleteButton.classes()).not.toContain('cursor-not-allowed')
  })

  it('validates required fields', async () => {
    // Создаем wrapper с пустыми данными
    wrapper = mount(LocationInput, {
      props: {
        location: {
          ...mockLocation,
          name: '',
          city: '',
          street: '',
          houseNumber: ''
        },
        index: 0
      }
    })
    
    await nextTick()
    
    // Проверяем, что есть ошибки валидации
    expect(wrapper.find('.text-red-600').exists()).toBe(true)
    
    const errorMessages = wrapper.findAll('.text-red-600')
    expect(errorMessages.length).toBeGreaterThan(0)
  })

  it('validates latitude range', async () => {
    const latitudeInput = wrapper.find('input[placeholder="55.7558"]')
    
    // Некорректная широта
    await latitudeInput.setValue(100)
    await wrapper.vm.updateLocation()
    await nextTick()
    
    expect(wrapper.find('.text-red-600').exists()).toBe(true)
    expect(wrapper.find('.text-red-600').text()).toContain('Широта должна быть от -90 до 90')
    
    // Корректная широта
    await latitudeInput.setValue(45.123)
    await wrapper.vm.updateLocation()
    await nextTick()
    
    expect(wrapper.find('.text-red-600').exists()).toBe(false)
  })

  it('validates longitude range', async () => {
    const longitudeInput = wrapper.find('input[placeholder="37.6173"]')
    
    // Некорректная долгота
    await longitudeInput.setValue(200)
    await wrapper.vm.updateLocation()
    await nextTick()
    
    expect(wrapper.find('.text-red-600').exists()).toBe(true)
    expect(wrapper.find('.text-red-600').text()).toContain('Долгота должна быть от -180 до 180')
    
    // Корректная долгота
    await longitudeInput.setValue(37.6173)
    await wrapper.vm.updateLocation()
    await nextTick()
    
    expect(wrapper.find('.text-red-600').exists()).toBe(false)
  })

  it('validates house number format', async () => {
    const houseNumberInput = wrapper.find('input[placeholder="15"]')
    
    // Некорректный номер дома
    await houseNumberInput.setValue('abc')
    await wrapper.vm.updateLocation()
    await nextTick()
    
    expect(wrapper.find('.text-red-600').exists()).toBe(true)
    expect(wrapper.find('.text-red-600').text()).toContain('Номер дома должен быть числом')
    
    // Корректный номер дома
    await houseNumberInput.setValue('15А')
    await wrapper.vm.updateLocation()
    await nextTick()
    
    expect(wrapper.find('.text-red-600').exists()).toBe(false)
  })

 

  it('handles priority selection', async () => {
    const priorityInputs = wrapper.findAll('input[type="radio"]')
    expect(priorityInputs.length).toBe(3)
    
    // Выбираем "Высокий" приоритет
    const highPriority = priorityInputs[2]
    await highPriority.setValue()
    
    expect(wrapper.emitted('update')).toBeTruthy()
    if (wrapper.emitted('update')) {
      const updateEvent = wrapper.emitted('update')!.slice(-1)[0][0]
      expect(updateEvent.priority).toBe('high')
    }
  })

  it('formats address with city starting with capital', () => {
    const formattedCity = wrapper.vm.formatCity('санкт-петербург')
    expect(formattedCity).toBe('Санкт-Петербург')
    
    const formattedMultiWord = wrapper.vm.formatCity('нижний новгород')
    expect(formattedMultiWord).toBe('Нижний Новгород')
  })
})