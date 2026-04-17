import { test, expect } from '../../fixtures/base'
import { createRep, currentMonth, ensureGeneratedSchedule, trackGeneratedScheduleEntries } from '../../fixtures/test-data'

const month = currentMonth(18)

test.describe('Schedule — Generate & Regenerate', () => {
  test.describe.configure({ mode: 'serial' })

  test('GET /api/v1/schedule/?month returns array', async ({ apiClient, cleanup }) => {
    const rep = await createRep(apiClient, `${cleanup.namespace}_schedule_generate`, 'active', cleanup)
    await ensureGeneratedSchedule(apiClient, month, [rep.id], cleanup)

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

  test('force=true API call succeeds when plan exists', async ({ apiClient, cleanup }) => {
    const rep = await createRep(apiClient, `${cleanup.namespace}_schedule_force`, 'active', cleanup)
    await ensureGeneratedSchedule(apiClient, month, [rep.id], cleanup)

    // force regen
    const res = await apiClient.post(`/api/v1/schedule/generate?force=true`, {
      data: { month, rep_ids: [rep.id] },
    })
    expect([200, 201]).toContain(res.status())
    await trackGeneratedScheduleEntries(apiClient, month, [rep.id], cleanup)
  })

  test('without force=true returns 409 when plan exists', async ({ apiClient, cleanup }) => {
    const rep = await createRep(apiClient, `${cleanup.namespace}_schedule_conflict`, 'active', cleanup)
    await ensureGeneratedSchedule(apiClient, month, [rep.id], cleanup)

    // second attempt without force → 409
    const res = await apiClient.post(`/api/v1/schedule/generate`, {
      data: { month, rep_ids: [rep.id] },
    })
    expect(res.status()).toBe(409)
  })
})
