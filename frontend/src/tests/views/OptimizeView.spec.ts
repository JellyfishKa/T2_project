import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import OptimizeView from '@/views/OptimizeView.vue'
import { createRouter, createMemoryHistory } from 'vue-router'
import { nextTick } from 'vue'

// Mock components
const MockOptimizationForm = {
  template: '<div>OptimizationForm Mock</div>',
  methods: {
    resetForm: vi.fn(),
    getFormData: vi.fn(() => ({ routeName: 'Test', locations: [] }))
  }
}

const MockConstraintsPanel = {
  template: '<div>ConstraintsPanel Mock</div>',
  emits: ['update-constraints']
}

const MockFileUpload = {
  template: '<div>FileUpload Mock</div>',
  emits: ['add-locations']
}

describe('OptimizeView.vue', () => {
  let wrapper: any
  
  beforeEach(() => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/optimize', component: OptimizeView }
      ]
    })
    
    wrapper = mount(OptimizeView, {
      global: {
        plugins: [router],
        stubs: {
          OptimizationForm: MockOptimizationForm,
          ConstraintsPanel: MockConstraintsPanel,
          FileUpload: MockFileUpload
        }
      }
    })
  })

 

  it('displays model selection options', () => {
    const modelLabels = wrapper.findAll('div.text-sm.font-medium')
    
    expect(wrapper.text()).toContain('Llama')
    expect(wrapper.text()).toContain('Qwen')
    expect(wrapper.text()).toContain('T-Pro')
    
    // Проверяем описания моделейs
    expect(wrapper.text()).toContain('Высокая точность, платный')
    expect(wrapper.text()).toContain('Быстрый, бесплатный')
    expect(wrapper.text()).toContain('Баланс цены и качества')
  })

  it('selects Llama model by default', () => {
    const llamaRadio = wrapper.find('input[value="llama"]')
    expect((llamaRadio.element as HTMLInputElement).checked).toBe(true)
  })

  it('changes selected model when clicked', async () => {
    const qwenRadio = wrapper.find('input[value="qwen"]')
    await qwenRadio.setValue()
    
    expect(wrapper.vm.selectedModel).toBe('qwen')
  })

  it('handles form validation updates', async () => {
    const optimizationForm = wrapper.findComponent({ name: 'OptimizationForm' })
  

    

    expect(wrapper.vm.isFormValid).toBe(false)
  })

  



  it('disables optimize button when form is invalid', async () => {
    // Устанавливаем невалидную форму
    wrapper.vm.isFormValid = false
    await nextTick()
    
    const optimizeButton = wrapper.find('button.bg-blue-600')
    expect(optimizeButton.attributes('disabled')).toBe('')
    expect(optimizeButton.classes()).toContain('disabled:opacity-50')
  })

  it('enables optimize button when form is valid', async () => {
    // Устанавливаем валидную форму
    wrapper.vm.isFormValid = true
    await nextTick()
    
    const optimizeButton = wrapper.find('button.bg-blue-600')
    expect(optimizeButton.attributes('disabled')).toBeUndefined()
  })

  it('shows alert when optimizing with invalid form', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    
    wrapper.vm.isFormValid = false
    await wrapper.vm.handleOptimize()
    
    expect(alertSpy).toHaveBeenCalledWith('Пожалуйста, заполните все обязательные поля формы')
    alertSpy.mockRestore()
  })

  it('resets form when reset button is clicked', async () => {
    const resetButton = wrapper.find('button.bg-white')
    await resetButton.trigger('click')
    
    // Проверяем, что модель сбросилась к Llama
    expect(wrapper.vm.selectedModel).toBe('llama')
    
    // Проверяем, что constraints сбросились к значениям по умолчанию
    expect(wrapper.vm.constraints).toEqual({
      vehicleCapacity: 1,
      maxDistance: 500,
      startTime: '08:00',
      endTime: '20:00'
    })
  })

  it('displays model characteristics', () => {
    expect(wrapper.text()).toContain('Llama: Высокая точность, платный')
    expect(wrapper.text()).toContain('Qwen: Быстрый, бесплатный')
    expect(wrapper.text()).toContain('T-Pro: Баланс цены и качества')
  })

  it('shows form requirements information', () => {
    expect(wrapper.text()).toContain('Все поля обязательны для заполнения')
    expect(wrapper.text()).toContain('Минимум 2 магазина для оптимизации маршрута')
  })
})