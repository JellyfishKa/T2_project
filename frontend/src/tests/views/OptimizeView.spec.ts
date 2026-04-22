import { flushPromises, mount, VueWrapper } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import OptimizeView from '@/views/OptimizeView.vue'
import type { RouteVariant } from '@/services/types'
import {
  optimizeVariants,
  fetchRoutePreview,
  confirmVariant,
} from '@/services/api'

vi.mock('@/services/api', () => ({
  optimizeVariants: vi.fn(),
  fetchRoutePreview: vi.fn(),
  confirmVariant: vi.fn(),
}))

vi.mock('@/components/RouteMap.vue', () => ({
  default: { name: 'RouteMap', render: () => null },
}))

vi.mock('@/components/optimize/OptimizationForm.vue', () => ({
  default: {
    name: 'OptimizationForm',
    template: '<div data-testid="optimization-form"></div>',
    emits: ['submit', 'validate'],
    methods: {
      resetForm: vi.fn(),
      getFormData: vi.fn(() => ({
        routeName: 'Тестовый маршрут',
        locations: [
          {
            id: 'loc-1',
            name: 'Store 1',
            city: 'Саранск',
            street: 'Ленина',
            houseNumber: '1',
            latitude: 54.1871,
            longitude: 45.1749,
            timeWindowStart: '09:00',
            timeWindowEnd: '18:00',
            priority: 'medium',
            address: 'г. Саранск, ул. Ленина, д. 1',
          },
          {
            id: 'loc-2',
            name: 'Store 2',
            city: 'Саранск',
            street: 'Советская',
            houseNumber: '5',
            latitude: 54.1902,
            longitude: 45.1685,
            timeWindowStart: '09:00',
            timeWindowEnd: '18:00',
            priority: 'medium',
            address: 'г. Саранск, ул. Советская, д. 5',
          },
          {
            id: 'loc-3',
            name: 'Store 3',
            city: 'Саранск',
            street: 'Пролетарская',
            houseNumber: '9',
            latitude: 54.175,
            longitude: 45.183,
            timeWindowStart: '09:00',
            timeWindowEnd: '18:00',
            priority: 'medium',
            address: 'г. Саранск, ул. Пролетарская, д. 9',
          },
        ],
      })),
      clearAllLocations: vi.fn(),
      addLocationFromImport: vi.fn(),
    }
  }
}))

vi.mock('@/components/optimize/OptimizationResult.vue', () => ({
  default: {
    name: 'OptimizationResult',
    template: '<div data-testid="optimization-result"></div>',
    props: [
      'result',
      'isLoading',
      'error',
      'originalMetrics',
      'locations',
      'originalLocationIds',
      'routeSource',
      'routeLabel',
      'isUpdatingMetrics',
      'canRestoreOriginal',
      'canRestoreAi',
      'aiRouteLabel',
      'originalRouteSource',
      'originalTrafficLightsCount',
      'currentRouteSource',
      'currentTrafficLightsCount',
      'llmEvaluationStatus',
      'llmQualityScore',
    ],
    emits: ['reset', 'retry', 'save', 'move-location', 'reorder-locations', 'restore-original', 'restore-ai'],
  }
}))

vi.mock('@/components/optimize/OptimizationVariants.vue', () => ({
  default: {
    name: 'OptimizationVariants',
    template: '<div data-testid="optimization-variants"></div>',
    props: ['variants', 'locations', 'modelUsed', 'llmEvaluationSuccess', 'responseTimeMs'],
    emits: ['select', 'reset'],
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

vi.mock('@/components/optimize/OptimizationProgress.vue', () => ({
  default: {
    name: 'OptimizationProgress',
    template: '<div data-testid="optimization-progress"></div>',
    props: ['model', 'done'],
  }
}))

describe('OptimizeView.vue', () => {
  let wrapper: VueWrapper<any>

  const mockedOptimizeVariants = vi.mocked(optimizeVariants)
  const mockedFetchRoutePreview = vi.mocked(fetchRoutePreview)
  const mockedConfirmVariant = vi.mocked(confirmVariant)

  const variant: RouteVariant = {
    id: 2,
    name: 'Вариант 2',
    description: 'Более быстрый маршрут',
    algorithm: 'nearest_neighbor',
    pros: ['короче'],
    cons: [],
    locations: ['loc-2', 'loc-1', 'loc-3'],
    metrics: {
      distance_km: 12.4,
      time_hours: 1.8,
      cost_rub: 740,
      quality_score: 91,
    }
  }

  beforeEach(() => {
    vi.useFakeTimers()
    vi.resetAllMocks()

    mockedFetchRoutePreview.mockResolvedValue({
      geometry: [],
      distance_km: 19.2,
      time_minutes: 84,
      cost_rub: 980,
      traffic_lights_count: 5,
      source: 'road_network',
      transport_mode: 'car' as const,
    })
    mockedOptimizeVariants.mockResolvedValue({
      variants: [variant],
      model_used: 'qwen',
      response_time_ms: 800,
      llm_evaluation_success: true,
    })
    mockedConfirmVariant.mockResolvedValue({
      id: 'route-1',
      name: 'saved',
      locations: variant.locations,
      total_distance_km: variant.metrics.distance_km,
      total_time_hours: variant.metrics.time_hours,
      total_cost_rub: variant.metrics.cost_rub,
      model_used: 'qwen',
      fallback_reason: null,
      has_comparison: true,
      created_at: new Date().toISOString(),
    } as any)

    wrapper = mount(OptimizeView)
    wrapper.vm.optimizationForm = {
      resetForm: vi.fn(),
      getFormData: () => ({
        routeName: 'Тестовый маршрут',
        locations: [
          {
            id: 'loc-1',
            name: 'Store 1',
            city: 'Саранск',
            street: 'Ленина',
            houseNumber: '1',
            latitude: 54.1871,
            longitude: 45.1749,
            timeWindowStart: '09:00',
            timeWindowEnd: '18:00',
            priority: 'medium',
            address: 'г. Саранск, ул. Ленина, д. 1',
          },
          {
            id: 'loc-2',
            name: 'Store 2',
            city: 'Саранск',
            street: 'Советская',
            houseNumber: '5',
            latitude: 54.1902,
            longitude: 45.1685,
            timeWindowStart: '09:00',
            timeWindowEnd: '18:00',
            priority: 'medium',
            address: 'г. Саранск, ул. Советская, д. 5',
          },
          {
            id: 'loc-3',
            name: 'Store 3',
            city: 'Саранск',
            street: 'Пролетарская',
            houseNumber: '9',
            latitude: 54.175,
            longitude: 45.183,
            timeWindowStart: '09:00',
            timeWindowEnd: '18:00',
            priority: 'medium',
            address: 'г. Саранск, ул. Пролетарская, д. 9',
          },
        ],
      }),
      clearAllLocations: vi.fn(),
      addLocationFromImport: vi.fn(),
    }
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('загружает варианты и считает исходные метрики маршрута', async () => {
    wrapper.vm.isFormValid = true

    const optimizePromise = wrapper.vm.handleOptimize()
    await vi.runAllTimersAsync()
    await optimizePromise
    await flushPromises()

    expect(mockedFetchRoutePreview).toHaveBeenCalledTimes(1)
    expect(mockedOptimizeVariants).toHaveBeenCalledWith(
      ['loc-1', 'loc-2', 'loc-3'],
      'qwen',
      expect.objectContaining({
        vehicle_capacity: 1,
        max_distance_km: 500,
      })
    )
    expect(wrapper.vm.originalMetrics).toEqual({
      total_distance_km: 19.2,
      total_time_hours: 2.15,
      total_cost_rub: 980,
      source: 'road_network',
      traffic_lights_count: 5,
    })
    expect(wrapper.vm.originalRouteSource).toBe('road_network')
    expect(wrapper.vm.originalTrafficLightsCount).toBe(5)
    expect(wrapper.vm.currentView).toBe('variants')
  })

  it('показывает статус fallback, если preview не удалось получить', async () => {
    wrapper.vm.routeName = 'Тестовый маршрут'
    wrapper.vm.formLocations = [
      {
        id: 'loc-1',
        name: 'Store 1',
        address: 'Address 1',
        lat: 54.1871,
        lon: 45.1749,
        time_window_start: '09:00',
        time_window_end: '18:00',
      },
      {
        id: 'loc-2',
        name: 'Store 2',
        address: 'Address 2',
        lat: 54.1902,
        lon: 45.1685,
        time_window_start: '09:00',
        time_window_end: '18:00',
      },
    ]
    wrapper.vm.originalLocationIds = ['loc-1', 'loc-2']
    wrapper.vm.variantsResponse = {
      variants: [variant],
      model_used: 'qwen',
      response_time_ms: 800,
      llm_evaluation_success: true,
    }
    wrapper.vm.optimizationResult = {
      id: 'route-1',
      name: 'Тестовый маршрут',
      locations: ['loc-1', 'loc-2'],
      total_distance_km: 19.2,
      total_time_hours: 1.4,
      total_cost_rub: 980,
      model_used: 'qwen',
      fallback_reason: null,
      has_comparison: false,
      created_at: new Date().toISOString(),
    }

    mockedFetchRoutePreview.mockRejectedValueOnce(new Error('preview failed'))
    wrapper.vm.handleReorderResultLocations({ fromIndex: 0, toIndex: 1 })
    await flushPromises()

    expect(wrapper.vm.currentRouteSource).toBe('client_fallback')
    expect(wrapper.vm.resultLlmEvaluationStatus).toBe('stale')
  })

  it('позволяет вручную перестраивать выбранный маршрут и откатывать его', async () => {
    wrapper.vm.routeName = 'Тестовый маршрут'
    wrapper.vm.formLocations = [
      {
        id: 'loc-1',
        name: 'Store 1',
        address: 'Address 1',
        lat: 54.1871,
        lon: 45.1749,
        time_window_start: '09:00',
        time_window_end: '18:00',
      },
      {
        id: 'loc-2',
        name: 'Store 2',
        address: 'Address 2',
        lat: 54.1902,
        lon: 45.1685,
        time_window_start: '09:00',
        time_window_end: '18:00',
      },
      {
        id: 'loc-3',
        name: 'Store 3',
        address: 'Address 3',
        lat: 54.175,
        lon: 45.183,
        time_window_start: '09:00',
        time_window_end: '18:00',
      },
    ]
    wrapper.vm.originalLocationIds = ['loc-1', 'loc-2', 'loc-3']
    wrapper.vm.variantsResponse = {
      variants: [variant],
      model_used: 'qwen',
      response_time_ms: 800,
      llm_evaluation_success: true,
    }

    wrapper.vm.handleVariantSelect(variant)
    expect(wrapper.vm.optimizationResult.locations).toEqual(['loc-2', 'loc-1', 'loc-3'])
    expect(wrapper.vm.resultRouteSource).toBe('ai')

    mockedFetchRoutePreview.mockResolvedValueOnce({
      geometry: [],
      distance_km: 16.6,
      time_minutes: 70,
      cost_rub: 860,
      traffic_lights_count: 4,
      source: 'road_network',
      transport_mode: 'car' as const,
    })
    wrapper.vm.handleMoveResultLocation({ index: 0, direction: 1 })
    await flushPromises()

    expect(wrapper.vm.optimizationResult.locations).toEqual(['loc-1', 'loc-2', 'loc-3'])
    expect(wrapper.vm.optimizationResult.total_distance_km).toBe(16.6)
    expect(wrapper.vm.resultRouteSource).toBe('manual')

    mockedFetchRoutePreview.mockResolvedValueOnce({
      geometry: [],
      distance_km: 12.4,
      time_minutes: 108,
      cost_rub: 740,
      traffic_lights_count: 5,
      source: 'road_network',
      transport_mode: 'car' as const,
    })
    wrapper.vm.restoreAiRoute()
    await flushPromises()

    expect(wrapper.vm.optimizationResult.locations).toEqual(['loc-2', 'loc-1', 'loc-3'])
    expect(wrapper.vm.resultRouteSource).toBe('ai')

    mockedFetchRoutePreview.mockResolvedValueOnce({
      geometry: [],
      distance_km: 19.2,
      time_minutes: 84,
      cost_rub: 980,
      traffic_lights_count: 5,
      source: 'road_network',
      transport_mode: 'car' as const,
    })
    wrapper.vm.restoreOriginalRoute()
    await flushPromises()

    expect(wrapper.vm.optimizationResult.locations).toEqual(['loc-1', 'loc-2', 'loc-3'])
    expect(wrapper.vm.resultRouteSource).toBe('original')
    expect(wrapper.vm.canRestoreAi).toBe(true)
  })

  it('сохраняет текущий ручной маршрут с актуальными метриками', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    wrapper.vm.originalLocationIds = ['loc-1', 'loc-2', 'loc-3']
    wrapper.vm.originalMetrics = {
      total_distance_km: 19.2,
      total_time_hours: 2.15,
      total_cost_rub: 980,
    }
    wrapper.vm.variantsResponse = {
      variants: [variant],
      model_used: 'qwen',
      response_time_ms: 800,
      llm_evaluation_success: true,
    }
    wrapper.vm.optimizationResult = {
      id: 'manual-route',
      name: 'Тестовый маршрут (ручная перестановка)',
      locations: ['loc-1', 'loc-3', 'loc-2'],
      total_distance_km: 17.5,
      total_time_hours: 1.9,
      total_cost_rub: 910,
      model_used: 'qwen',
      fallback_reason: null,
      has_comparison: false,
      created_at: new Date().toISOString(),
    }
    wrapper.vm.selectedAiVariantLocationIds = ['loc-2', 'loc-1', 'loc-3']
    wrapper.vm.selectedAiVariantQualityScore = 91

    await wrapper.vm.saveRoute()

    expect(mockedConfirmVariant).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Тестовый маршрут (ручная перестановка)',
        locations: ['loc-1', 'loc-3', 'loc-2'],
        quality_score: 0,
        original_location_ids: ['loc-1', 'loc-2', 'loc-3'],
        original_total_distance_km: 19.2,
        original_total_time_hours: 2.15,
        original_total_cost_rub: 980,
      })
    )
    expect(alertSpy).toHaveBeenCalledWith(
      'Маршрут успешно сохранён без LLM-оценки для текущего порядка.'
    )
    alertSpy.mockRestore()
  })
})
