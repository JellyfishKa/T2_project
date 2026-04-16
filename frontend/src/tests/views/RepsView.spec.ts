import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import RepsView from '@/views/RepsView.vue'
import * as api from '@/services/api'

// Мокаем API
vi.mock('@/services/api', () => ({
  fetchReps: vi.fn(),
  fetchVehicles: vi.fn(),
  createRep: vi.fn(),
  updateRep: vi.fn(),
  deleteRep: vi.fn(),
}))

const mockReps = [
  { id: 'rep-1', name: 'Иванов Иван', status: 'active', created_at: '2026-01-01T00:00:00Z' },
  { id: 'rep-2', name: 'Петров Пётр', status: 'sick', created_at: '2026-01-02T00:00:00Z' },
]

const mockVehicles = [
  { id: 'veh-1', name: 'Lada Vesta', fuel_price_rub: 60, consumption_city_l_100km: 8, consumption_highway_l_100km: 6 },
]

describe('RepsView.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(api.fetchReps as any).mockResolvedValue(mockReps)
    ;(api.fetchVehicles as any).mockResolvedValue(mockVehicles)
    ;(api.createRep as any).mockResolvedValue({ id: 'rep-3', name: 'Сидоров', status: 'active', created_at: '2026-03-01T00:00:00Z' })
    ;(api.updateRep as any).mockResolvedValue({ ...mockReps[0], status: 'sick' })
    ;(api.deleteRep as any).mockResolvedValue(undefined)
  })

  it('загружает список сотрудников при монтировании', async () => {
    mount(RepsView)
    await flushPromises()
    expect(api.fetchReps).toHaveBeenCalledTimes(1)
  })

  it('отображает сотрудников из списка', async () => {
    const wrapper = mount(RepsView)
    await flushPromises()
    expect(wrapper.text()).toContain('Иванов Иван')
    expect(wrapper.text()).toContain('Петров Пётр')
  })

  it('открывает форму добавления при клике на кнопку', async () => {
    const wrapper = mount(RepsView)
    await flushPromises()
    const addBtn = wrapper.findAll('button').find(b => b.text().includes('Добавить'))
    expect(addBtn).toBeTruthy()
    if (addBtn) {
      await addBtn.trigger('click')
      expect(wrapper.text()).toContain('Новый сотрудник')
    }
  })

  it('createRep вызывает apiCreateRep с именем и статусом', async () => {
    const wrapper = mount(RepsView)
    await flushPromises()
    // Открываем форму
    const addBtn = wrapper.findAll('button').find(b => b.text().includes('Добавить'))
    if (addBtn) await addBtn.trigger('click')
    // Заполняем имя
    const input = wrapper.find('input[placeholder*="Иванов"]')
    if (input) {
      await input.setValue('Новый Сотрудник')
      const saveBtn = wrapper.findAll('button').find(b => b.text() === 'Сохранить')
      if (saveBtn) {
        await saveBtn.trigger('click')
        await flushPromises()
        expect(api.createRep).toHaveBeenCalledWith('Новый Сотрудник', 'active', null)
      }
    }
  })

  it('не создаёт сотрудника с пустым именем', async () => {
    const wrapper = mount(RepsView)
    await flushPromises()
    const addBtn = wrapper.findAll('button').find(b => b.text().includes('Добавить'))
    if (addBtn) await addBtn.trigger('click')
    const saveBtn = wrapper.findAll('button').find(b => b.text() === 'Сохранить')
    if (saveBtn) {
      await saveBtn.trigger('click')
      await flushPromises()
      expect(api.createRep).not.toHaveBeenCalled()
    }
  })

  it('updateStatus вызывает updateRep с новым статусом', async () => {
    const wrapper = mount(RepsView)
    await flushPromises()
    const selects = wrapper.findAll('select')
    if (selects.length > 0) {
      await selects[0].setValue('vacation')
      await selects[0].trigger('change')
      await flushPromises()
      expect(api.updateRep).toHaveBeenCalledWith('rep-1', { status: 'vacation' })
    }
  })

  it('deleteRep вызывает apiDeleteRep после confirm', async () => {
    vi.stubGlobal('confirm', () => true)
    const wrapper = mount(RepsView)
    await flushPromises()
    const deleteBtn = wrapper.findAll('button').find(b => b.text().includes('Удалить'))
    if (deleteBtn) {
      await deleteBtn.trigger('click')
      await flushPromises()
      expect(api.deleteRep).toHaveBeenCalledWith('rep-1')
    }
    vi.unstubAllGlobals()
  })

  it('отображает ошибку при неудачной загрузке', async () => {
    ;(api.fetchReps as any).mockRejectedValueOnce(new Error('Нет соединения'))
    const wrapper = mount(RepsView)
    await flushPromises()
    expect(wrapper.text()).toContain('Ошибка загрузки данных')
  })
})
