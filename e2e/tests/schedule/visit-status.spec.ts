import { test, expect } from '../../fixtures/base'
import { createRep, currentMonth, ensureGeneratedSchedule, type RepData } from '../../fixtures/test-data'

const month = currentMonth(20)

let seedRep: RepData | null = null

test.describe('Schedule — Visit Status Transitions', () => {
  test.describe.configure({ mode: 'serial' })

  test.beforeEach(async ({ apiClient, cleanup }) => {
    seedRep = await createRep(apiClient, `${cleanup.namespace}_visit_status`, 'active', cleanup)
    await ensureGeneratedSchedule(apiClient, month, [seedRep.id], cleanup)
  })

  test('PATCH visit to completed succeeds', async ({ apiClient }) => {
    const res = await apiClient.get(`/api/v1/schedule/?month=${month}`)
    expect(res.status()).toBe(200)
    const body = await res.json()
    const visits: any[] = body.routes?.flatMap((r: any) => r.visits) ?? []
    const planned = visits.find((v: any) => v.status === 'planned')
    if (!planned) return test.skip()

    const patch = await apiClient.patch(`/api/v1/schedule/${planned.id}`, {
      data: { status: 'completed' },
    })
    expect([200, 201]).toContain(patch.status())
    const updated = await patch.json()
    expect(updated.status).toBe('completed')
  })

  test('PATCH visit to skipped succeeds', async ({ apiClient }) => {
    const res = await apiClient.get(`/api/v1/schedule/?month=${month}`)
    const body = await res.json()
    const visits: any[] = body.routes?.flatMap((r: any) => r.visits) ?? []
    const planned = visits.find((v: any) => v.status === 'planned')
    if (!planned) return test.skip()

    const patch = await apiClient.patch(`/api/v1/schedule/${planned.id}`, {
      data: { status: 'skipped' },
    })
    expect([200, 201]).toContain(patch.status())
  })

  test('invalid transition completed→planned returns 422', async ({ apiClient }) => {
    const res = await apiClient.get(`/api/v1/schedule/?month=${month}`)
    const body = await res.json()
    const visits: any[] = body.routes?.flatMap((r: any) => r.visits) ?? []
    const planned = visits.find((v: any) => v.status === 'planned')
    if (!planned) return test.skip()

    await apiClient.patch(`/api/v1/schedule/${planned.id}`, {
      data: { status: 'completed' },
    })

    const invalid = await apiClient.patch(`/api/v1/schedule/${planned.id}`, {
      data: { status: 'planned' },
    })
    expect(invalid.status()).toBe(422)
  })
})
