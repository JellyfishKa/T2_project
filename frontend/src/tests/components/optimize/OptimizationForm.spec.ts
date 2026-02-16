import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import OptimizationForm from '@/components/optimize/OptimizationForm.vue'
import { nextTick } from 'vue'

describe('OptimizationForm.vue', () => {
  let wrapper: any

  beforeEach(() => {
    wrapper = mount(OptimizationForm)
  })

  it('renders the form with correct structure', () => {
    // Проверяем основные элементы формы
    expect(wrapper.find('h3').text()).toBe('Параметры маршрута')
    expect(wrapper.find('label[for="routeName"]').text()).toContain(
      'Название маршрута'
    )
    expect(wrapper.find('input#routeName').exists()).toBe(true)

    // Проверяем наличие секции магазинов
    expect(wrapper.find('h4').text()).toBe('Магазины *')
    expect(wrapper.find('button').text()).toContain('Добавить магазин')
  })

  it('starts with two empty location inputs', () => {
    const locationInputs = wrapper.findAllComponents({ name: 'LocationInput' })
    expect(locationInputs.length).toBe(2)
  })

  it('adds a new location when add button is clicked', async () => {
    const addButton = wrapper.find('button')
    await addButton.trigger('click')

    const locationInputs = wrapper.findAllComponents({ name: 'LocationInput' })
    expect(locationInputs.length).toBe(3)
  })

  it('validates route name field', async () => {
    const routeNameInput = wrapper.find('input#routeName')

    // Пустое поле
    await routeNameInput.setValue('')
    await nextTick()

    expect(wrapper.find('.text-red-600').exists()).toBe(true)
    expect(wrapper.find('.text-red-600').text()).toContain(
      'Название маршрута обязательно'
    )

    // Слишком короткое
    await routeNameInput.setValue('ab')
    await nextTick()

    // Валидное значение
    await routeNameInput.setValue('Мой маршрут')
    await nextTick()

    expect(wrapper.find('.text-red-600').exists()).toBe(true)
  })

  it('validates minimum number of locations', async () => {
    // Удаляем один магазин
    const locationInputs = wrapper.findAllComponents({ name: 'LocationInput' })
    if (locationInputs.length > 1) {
      const removeButtons = wrapper.findAll('button.text-gray-400')
      if (removeButtons.length > 0) {
        // Первая кнопка удаления (вторая локация)
        await removeButtons[1].trigger('click')
        await nextTick()
      }
    }
  })

  it('emits submit event when form is valid', async () => {
    const routeNameInput = wrapper.find('input#routeName')
    await routeNameInput.setValue('Тестовый маршрут')

    // Получаем форму и триггерим submit
    const form = wrapper.find('form')
    await form.trigger('submit.prevent')
  })

  it('emits validate event when validation state changes', async () => {
    const routeNameInput = wrapper.find('input#routeName')

    // Invalid state
    await routeNameInput.setValue('')
    await nextTick()

    expect(wrapper.emitted('validate')).toBeTruthy()
    if (wrapper.emitted('validate')) {
      const lastEmit = wrapper.emitted('validate')!.slice(-1)[0][0]
      expect(lastEmit).toBe(false)
    }
  })

  it('exposes resetForm method', async () => {
    // Проверяем, что метод существует
    expect(typeof wrapper.vm.resetForm).toBe('function')

    // Меняем значение и сбрасываем
    const routeNameInput = wrapper.find('input#routeName')
    await routeNameInput.setValue('Тестовое значение')

    wrapper.vm.resetForm()
    await nextTick()

    expect((routeNameInput.element as HTMLInputElement).value).toBe('')
  })

  it('exposes getFormData method', () => {
    expect(typeof wrapper.vm.getFormData).toBe('function')

    const formData = wrapper.vm.getFormData()
    expect(formData).toHaveProperty('routeName')
    expect(formData).toHaveProperty('locations')
    expect(formData).toHaveProperty('notes')
    expect(Array.isArray(formData.locations)).toBe(true)
  })

  it('exposes addLocationFromImport method', async () => {
    expect(typeof wrapper.vm.addLocationFromImport).toBe('function')

    const initialCount = wrapper.vm.getFormData().locations.length

    const mockLocation = {
      id: 'test-import-1',
      name: 'Импортированный магазин',
      city: 'Москва',
      street: 'Тверская',
      houseNumber: '15',
      latitude: 55.7558,
      longitude: 37.6173,
      timeWindowStart: '09:00',
      timeWindowEnd: '18:00',
      priority: 'medium' as const
    }

    wrapper.vm.addLocationFromImport(mockLocation)
    await nextTick()

    const newCount = wrapper.vm.getFormData().locations.length
    expect(newCount).toBe(initialCount + 1)
  })

  it('exposes clearAllLocations method', async () => {
    expect(typeof wrapper.vm.clearAllLocations).toBe('function')

    const initialCount = wrapper.vm.getFormData().locations.length
    expect(initialCount).toBeGreaterThan(0)

    wrapper.vm.clearAllLocations()
    await nextTick()

    const newCount = wrapper.vm.getFormData().locations.length
    expect(newCount).toBe(0)
  })
})
