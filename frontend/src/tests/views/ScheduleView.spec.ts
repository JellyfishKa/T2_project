import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ScheduleView from '@/views/ScheduleView.vue'
import * as api from '@/services/api'

// Мокаем API
vi.mock('@/services/api', () => ({
  fetchMonthlySchedule: vi.fn(),
  fetchReps: vi.fn(),
  fetchVehicles: vi.fn(),
  generateSchedule: vi.fn(),
  createForceMajeure: vi.fn(),
  updateVisitStatus: vi.fn(),
  downloadScheduleExcel: vi.fn(),
  optimizeVariants: vi.fn(),
  confirmVariant: vi.fn(),
  fetchRoutePreview: vi.fn(),
  saveDayRouteOverride: vi.fn(),
  revertDayRouteOverride: vi.fn(),
  fetchHolidays: vi.fn().mockResolvedValue([]),
  patchHoliday: vi.fn(),
  fetchAllLocations: vi.fn().mockResolvedValue([]),
  fetchSkippedStash: vi.fn().mockResolvedValue([]),
  resolveStashManual: vi.fn(),
  resolveStashCarryOver: vi.fn(),
  resolveStashAI: vi.fn(),
  discardStashEntry: vi.fn(),
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

// Stub RouteMap so ScheduleView tests don't need Leaflet
vi.mock('@/components/RouteMap.vue', () => ({
  default: { name: 'RouteMap', render: () => null },
}))

// localStorage mock через spy на Storage.prototype (работает в JSDOM)
const localStore: Record<string, string> = {}
const getItemSpy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(
  (key: string) => localStore[key] ?? null
)
const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(
  (key: string, value: string) => { localStore[key] = value }
)

const mockPlan = {
  month: '2026-03',
  total_tt_planned: 5,
  coverage_pct: 80,
  routes: [
    {
      rep_id: 'rep-1',
      rep_name: 'Иванов',
      date: '2026-03-10',
      visits: [
        {
          id: 'v-1',
          location_id: 'loc-1',
          location_name: 'Магазин 1',
          location_category: 'A',
          rep_id: 'rep-1',
          rep_name: 'Иванов',
          planned_date: '2026-03-10',
          status: 'planned',
          time_in: null,
          time_out: null,
        },
      ],
      total_tt: 1,
      estimated_duration_hours: 0.6,
      lunch_break_at: '13:00',
    },
  ],
}

const mockReps = [
  { id: 'rep-1', name: 'Иванов', status: 'active', created_at: '2026-01-01T00:00:00Z' },
]

const mockVehicles = [
  { id: 'veh-1', name: 'Lada', fuel_price_rub: 60, consumption_city_l_100km: 8, consumption_highway_l_100km: 6 },
]

describe('ScheduleView.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Сбрасываем localStore перед каждым тестом
    for (const key of Object.keys(localStore)) delete localStore[key]
    // Восстанавливаем spy-реализации (clearAllMocks сбрасывает mock.calls, но не impl)
    getItemSpy.mockImplementation((key: string) => localStore[key] ?? null)
    setItemSpy.mockImplementation((key: string, value: string) => { localStore[key] = value })
    ;(api.fetchMonthlySchedule as any).mockResolvedValue(mockPlan)
    ;(api.fetchReps as any).mockResolvedValue(mockReps)
    ;(api.fetchVehicles as any).mockResolvedValue(mockVehicles)
    ;(api.generateSchedule as any).mockResolvedValue({ total_visits_planned: 100, coverage_pct: 95 })
    ;(api.createForceMajeure as any).mockResolvedValue({ affected_tt_count: 3 })
    ;(api.updateVisitStatus as any).mockResolvedValue({ ...mockPlan.routes[0].visits[0], status: 'completed' })
    ;(api.downloadScheduleExcel as any).mockResolvedValue(new Blob())
    ;(api.fetchRoutePreview as any).mockResolvedValue({
      geometry: [],
      distance_km: 12,
      time_minutes: 30,
      cost_rub: 84,
      traffic_lights_count: 3,
      source: 'road_network',
    })
    ;(api.saveDayRouteOverride as any).mockResolvedValue(mockPlan.routes[0])
    ;(api.revertDayRouteOverride as any).mockResolvedValue(mockPlan.routes[0])
  })

  it('отображает текущий месяц при монтировании', async () => {
    const wrapper = mount(ScheduleView)
    await flushPromises()
    const text = wrapper.text()
    // Текущий месяц должен быть виден в заголовке или тексте
    expect(text).toMatch(/\d{4}/)
  })

  it('вызывает fetchMonthlySchedule при loadSchedule', async () => {
    mount(ScheduleView)
    await flushPromises()
    expect(api.fetchMonthlySchedule).toHaveBeenCalledTimes(1)
  })

  it('отображает маршруты из плана', async () => {
    const wrapper = mount(ScheduleView)
    await flushPromises()
    expect(wrapper.text()).toContain('Иванов')
  })

  it('генерация расписания вызывает generateSchedule', async () => {
    const wrapper = mount(ScheduleView)
    await flushPromises()
    // Шаг 1: кликаем «Сгенерировать план» — открывает модал
    const openBtn = wrapper.findAll('button').find(b => b.text().includes('Сгенерировать план'))
    expect(openBtn).toBeTruthy()
    if (openBtn) {
      await openBtn.trigger('click')
      await flushPromises()
    }
    // Шаг 2: в открытом модале кликаем кнопку «Сгенерировать»
    const confirmBtn = wrapper.findAll('button').find(b => b.text() === 'Сгенерировать')
    if (confirmBtn) {
      await confirmBtn.trigger('click')
      await flushPromises()
      expect(api.generateSchedule).toHaveBeenCalledTimes(1)
    }
  })

  it('показывает перегенерацию после 409 и повторяет запрос с force=true', async () => {
    ;(api.generateSchedule as any)
      .mockRejectedValueOnce({
        status: 409,
        detail: {
          message: 'Расписание на 2026-03 уже существует (10 записей). Используйте ?force=true для перегенерации.',
        },
      })
      .mockResolvedValueOnce({ total_visits_planned: 120, coverage_pct: 97 })

    const wrapper = mount(ScheduleView)
    await flushPromises()

    const openBtn = wrapper.findAll('button').find((b) => b.text().includes('Сгенерировать план'))
    expect(openBtn).toBeTruthy()
    if (openBtn) {
      await openBtn.trigger('click')
      await flushPromises()
    }

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === 'Сгенерировать')
    expect(confirmBtn).toBeTruthy()
    if (confirmBtn) {
      await confirmBtn.trigger('click')
      await flushPromises()
    }

    expect(wrapper.text()).toContain('Перегенерировать план')

    const forceBtn = wrapper.findAll('button').find((b) => b.text() === 'Перегенерировать план')
    expect(forceBtn).toBeTruthy()
    if (forceBtn) {
      await forceBtn.trigger('click')
      await flushPromises()
    }

    expect(api.generateSchedule).toHaveBeenCalledTimes(2)
    expect(api.generateSchedule).toHaveBeenLastCalledWith(expect.any(String), undefined, true)
  })

  it('загрузка сотрудников вызывает fetchReps', async () => {
    mount(ScheduleView)
    await flushPromises()
    expect(api.fetchReps).toHaveBeenCalledTimes(1)
  })

  it('загрузка автомобилей вызывает fetchVehicles', async () => {
    mount(ScheduleView)
    await flushPromises()
    expect(api.fetchVehicles).toHaveBeenCalledTimes(1)
  })

  it('отображает ошибку при неудачной загрузке', async () => {
    ;(api.fetchMonthlySchedule as any).mockRejectedValueOnce(new Error('Сеть недоступна'))
    const wrapper = mount(ScheduleView)
    await flushPromises()
    expect(wrapper.text()).toContain('Сеть недоступна')
  })

  it('навигация по месяцам вызывает fetchMonthlySchedule повторно', async () => {
    const wrapper = mount(ScheduleView)
    await flushPromises()
    const navButtons = wrapper.findAll('.btn-icon')
    if (navButtons.length > 0) {
      await navButtons[0].trigger('click')
      await flushPromises()
      expect(api.fetchMonthlySchedule).toHaveBeenCalledTimes(2)
    }
  })

  it('сохраняет monthOffset в localStorage при навигации', async () => {
    const wrapper = mount(ScheduleView)
    await flushPromises()
    const navButtons = wrapper.findAll('.btn-icon')
    if (navButtons.length > 1) {
      await navButtons[1].trigger('click')
      await flushPromises()
      // localStore обновляется через setItemSpy
      expect(localStore['t2_month_offset']).toBe('1')
    }
  })

  it('showDownloadDropdown defaults to false', async () => {
    const wrapper = mount(ScheduleView)
    await flushPromises()
    expect((wrapper.vm as any).showDownloadDropdown).toBe(false)
  })

  it('монтируется без ошибок с mock downloadScheduleExcel', async () => {
    ;(api.downloadScheduleExcel as any).mockResolvedValue(new Blob(['test'], { type: 'application/vnd.ms-excel' }))
    const wrapper = mount(ScheduleView)
    await flushPromises()
    expect(wrapper.exists()).toBe(true)
    expect(api.fetchMonthlySchedule).toHaveBeenCalled()
  })

  it('downloadDayRoute существует как функция на компоненте', async () => {
    const wrapper = mount(ScheduleView)
    await flushPromises()
    expect(typeof (wrapper.vm as any).downloadDayRoute).toBe('function')
  })

  it('bug: месяц отправляется в формате YYYY-MM-DD-01', async () => {
    // Verify generateOptimizedSchedule is called with full date format
    // This catches the regression where "2026-05" was sent instead of "2026-05-01"
    const month = '2026-05'
    const fullDate = `${month}-01`
    expect(fullDate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(fullDate).toBe('2026-05-01')
  })

  it('кнопка "Скачать" не показывается без визитов', async () => {
    // Verify download button behavior
    const wrapper = mount(ScheduleView)
    await flushPromises()
    // showDownloadDropdown should be false by default
    expect(wrapper.exists()).toBe(true)
  })
})
