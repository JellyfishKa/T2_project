import { test, expect } from '../../fixtures/base'
import { currentMonth } from '../../fixtures/test-data'

test.describe('Holidays — Toggle Working Day', () => {
  test('GET /api/v1/holidays/?month returns array', async ({ apiClient }) => {
    const month = currentMonth()
    const res = await apiClient.get(`/api/v1/holidays/?month=${month}`)
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()
  })

  test('PATCH holiday toggles is_working and returns affected_visits_count', async ({ apiClient }) => {
    // Use January 2026 — guaranteed to have Russian holidays (New Year's Day)
    const month = '2026-01'
    const res = await apiClient.get(`/api/v1/holidays/?month=${month}`)
    const holidays = await res.json()
    if (!Array.isArray(holidays) || !holidays.length) return test.skip()

    const holiday = holidays[0]
    const originalIsWorking: boolean = holiday.is_working

    const patch = await apiClient.patch(`/api/v1/holidays/${holiday.date}`, {
      data: { is_working: !originalIsWorking },
    })
    expect(patch.status()).toBe(200)
    const updated = await patch.json()
    expect(updated.is_working).toBe(!originalIsWorking)
    expect(typeof updated.affected_visits_count).toBe('number')

    // restore
    await apiClient.patch(`/api/v1/holidays/${holiday.date}`, {
      data: { is_working: originalIsWorking },
    })
  })

  test('Holidays modal opens on schedule page', async ({ page }) => {
    await page.goto('/schedule')
    await page.click('text=Праздники')
    const modal = page.locator('[class*="modal"]').first()
    await expect(modal).toBeVisible({ timeout: 5_000 })
    // modal shows at least one item (holiday row or toggle)
    await expect(modal.locator('label, input[type="checkbox"], [class*="row"], li').first()).toBeVisible({ timeout: 5_000 })
  })
})
