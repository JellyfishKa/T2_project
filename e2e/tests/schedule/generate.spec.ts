import { test, expect } from '../../fixtures/base'
import { createRep, currentMonth, deleteRep, ensureGeneratedSchedule, RepData } from '../../fixtures/test-data'

const month = currentMonth(3)

let seedRep: RepData | null = null

test.describe('Schedule — Generate & Regenerate', () => {
  test.describe.configure({ mode: 'serial' })

  test.beforeEach(async ({ apiClient }) => {
    if (!seedRep) {
      seedRep = await createRep(apiClient, `E2E Schedule Generate ${Date.now()}`)
    }
  })

  test.afterAll(async ({ playwright }) => {
    if (!seedRep) return

    const apiClient = await playwright.request.newContext({
      baseURL: process.env.API_URL ?? 'http://127.0.0.1:8000',
      extraHTTPHeaders: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    })
    await deleteRep(apiClient, seedRep.id).catch(() => {})
    await apiClient.dispose()
    seedRep = null
  })

  test('GET /api/v1/schedule/?month returns array', async ({ apiClient }) => {
    await ensureGeneratedSchedule(apiClient, month, seedRep ? [seedRep.id] : [])

    const res = await apiClient.get(`/api/v1/schedule/?month=${month}`)
    expect([200, 404]).toContain(res.status())
    if (res.status() === 200) {
      const body = await res.json()
      expect(body).toHaveProperty('routes')
    }
  })

  test('schedule page loads and shows month navigation', async ({ page }) => {
    await page.goto('/schedule')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('button:has-text("Сгенерировать план")')).toBeVisible()
    await expect(page.locator('button:has-text("◀")')).toBeVisible()
    await expect(page.locator('button:has-text("▶")')).toBeVisible()
  })

  test('open generate modal → modal appears with Сгенерировать button', async ({ page }) => {
    await page.goto('/schedule')
    await page.click('text=Сгенерировать план')
    await expect(page.locator('[class*="modal"], [class*="overlay"]').first()).toBeVisible()
    await expect(page.locator('button:has-text("Сгенерировать")').last()).toBeVisible()
  })

  test('force=true API call succeeds when plan exists', async ({ apiClient }) => {
    if (!seedRep) throw new Error('Schedule seed rep was not created')

    await ensureGeneratedSchedule(apiClient, month, [seedRep.id])

    // force regen
    const res = await apiClient.post(`/api/v1/schedule/generate?force=true`, {
      data: { month, rep_ids: [seedRep.id] },
    })
    expect([200, 201]).toContain(res.status())
  })

  test('without force=true returns 409 when plan exists', async ({ apiClient }) => {
    if (!seedRep) throw new Error('Schedule seed rep was not created')

    await ensureGeneratedSchedule(apiClient, month, [seedRep.id])

    // second attempt without force → 409
    const res = await apiClient.post(`/api/v1/schedule/generate`, {
      data: { month, rep_ids: [seedRep.id] },
    })
    expect(res.status()).toBe(409)
  })
})
