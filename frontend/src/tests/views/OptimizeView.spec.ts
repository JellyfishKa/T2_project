import { mount, VueWrapper } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import OptimizeView from '@/views/OptimizeView.vue'
import { createRouter, createMemoryHistory } from 'vue-router'
import { nextTick } from 'vue'

// Мокаем API
vi.mock('@/services/api', () => ({
  optimize: vi.fn()
}))

// Мокаем компоненты
vi.mock('@/components/optimize/OptimizationForm.vue', () => ({
  default: {
    name: 'OptimizationForm',
    template: '<div data-testid="optimization-form"></div>',
    props: ['modelValue'],
    emits: ['submit', 'validate'],
    methods: {
      resetForm: vi.fn(),
      getFormData: vi.fn(() => ({
        routeName: 'Test Route',
        locations: [
          {
            id: 'loc-1',
            name: 'Store 1',
            city: 'Moscow',
            street: 'Tverskaya',
            houseNumber: '15',
            latitude: 55.7558,
            longitude: 37.6173,
            timeWindowStart: '09:00',
            timeWindowEnd: '18:00',
            priority: 'medium'
          }
        ]
      })),
      clearAllLocations: vi.fn(),
      addLocationFromImport: vi.fn()
    }
  }
}))

vi.mock('@/components/optimize/OptimizationResult.vue', () => ({
  default: {
    name: 'OptimizationResult',
    template: '<div data-testid="optimization-result"></div>',
    props: ['result', 'isLoading', 'error', 'originalMetrics', 'locations'],
    emits: ['reset', 'retry', 'save']
  }
}))

vi.mock('@/components/optimize/ConstraintsPanel.vue', () => ({
  default: {
    name: 'ConstraintsPanel',
    template: '<div data-testid="constraints-panel"></div>',
    props: ['constraints'],
    emits: ['update-constraints']
  }
}))

vi.mock('@/components/optimize/FileUpload.vue', () => ({
  default: {
    name: 'FileUpload',
    template: '<div data-testid="file-upload"></div>',
    emits: ['add-locations']
  }
}))

// Создаем роутер для тестов
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/optimize', component: OptimizeView }
  ]
})

describe('OptimizeView.vue', () => {
  let wrapper: VueWrapper<any>

  beforeEach(async () => {
    vi.resetAllMocks()

    wrapper = mount(OptimizeView, {
      global: {
        plugins: [router],
        stubs: {
          OptimizationForm: true,
          OptimizationResult: true,
          ConstraintsPanel: true,
          FileUpload: true
        }
      }
    })

    await router.push('/optimize')
    await router.isReady()
  })

  it('отображает выбор модели', () => {
    expect(wrapper.text()).toContain('Llama')
    expect(wrapper.text()).toContain('Qwen')
  })

  it('выбирает Llama модель по умолчанию', () => {
    const llamaRadio = wrapper.find('input[value="llama"]')
    expect((llamaRadio.element as HTMLInputElement).checked).toBe(true)
  })

  it('изменяет выбранную модель при клике', async () => {
    const qwenRadio = wrapper.find('input[value="qwen"]')
    await qwenRadio.setValue(true)

    expect(wrapper.vm.selectedModel).toBe('qwen')
  })

  it('отключает кнопку оптимизации при невалидной форме', async () => {
    wrapper.vm.isFormValid = false
    await nextTick()

    const optimizeButton = wrapper.find('button.bg-blue-600')
    expect(optimizeButton.attributes('disabled')).toBeDefined()
  })

  it('включает кнопку оптимизации при валидной форме', async () => {
    wrapper.vm.isFormValid = true
    await nextTick()

    const optimizeButton = wrapper.find('button.bg-blue-600')
    expect(optimizeButton.attributes('disabled')).toBeUndefined()
  })

  it('показывает предупреждение при попытке оптимизации с невалидной формой', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    wrapper.vm.isFormValid = false
    await wrapper.vm.handleOptimize()

    expect(alertSpy).toHaveBeenCalledWith(
      'Пожалуйста, заполните все обязательные поля формы'
    )
    alertSpy.mockRestore()
  })
})
