import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import DatabaseView from '@/views/DatabaseView.vue'
import * as api from '@/services/api'

vi.mock('@/services/api', () => ({
  fetchAllLocations: vi.fn(),
  fetchVehicles: vi.fn(),
  createVehicle: vi.fn(),
  deleteVehicle: vi.fn(),
  uploadVehiclesJson: vi.fn(),
  fetchReps: vi.fn(),
  createRep: vi.fn(),
  updateRep: vi.fn(),
  deleteRep: vi.fn(),
  uploadLocations: vi.fn(),
  previewClearLocations: vi.fn(),
  clearAllLocations: vi.fn(),
  fetchAuditLog: vi.fn(),
  getApiErrorMessage: vi.fn((error: any, fallback?: string) =>
    error?.response?.data?.detail?.message ??
    error?.response?.data?.detail ??
    error?.detail?.message ??
    error?.detail ??
    error?.message ??
    fallback ??
    'Произошла ошибка'
  ),
}))

function buildRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/database', component: DatabaseView },
    ],
  })
}

describe('DatabaseView.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(api.fetchAllLocations as any)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
    ;(api.fetchVehicles as any).mockResolvedValue([])
    ;(api.fetchReps as any).mockResolvedValue([])
    ;(api.fetchAuditLog as any).mockResolvedValue({ items: [], total: 0 })
  })

  it('keeps uploaded locations visible when follow-up fetch returns empty', async () => {
    ;(api.uploadLocations as any).mockResolvedValue({
      created: [
        {
          id: 'loc-1',
          name: 'Точка 1',
          lat: 54.1871,
          lon: 45.1749,
          time_window_start: '09:00',
          time_window_end: '18:00',
          category: 'A',
          city: 'Саранск',
          district: 'г.о. Саранск',
          address: 'ул. Советская, 35',
        },
      ],
      errors: [],
      total_processed: 1,
    })

    const router = buildRouter()
    await router.push('/database')
    await router.isReady()

    const wrapper = mount(DatabaseView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    const file = new File(['test'], 'locations.json', { type: 'application/json' })
    const fileInput = wrapper.find('input[type="file"]')
    expect(fileInput.exists()).toBe(true)

    Object.defineProperty(fileInput.element, 'files', {
      value: [file],
      configurable: true,
    })
    await fileInput.trigger('change')
    await flushPromises()

    expect(wrapper.text()).toContain('Загружено: 1')
    expect(wrapper.text()).toContain('Точка 1')
    expect(wrapper.text()).not.toContain('Нет локаций — загрузите файл')
  })
})
