import { test, expect } from '../../fixtures/base'
import { createRep, currentMonth } from '../../fixtures/test-data'

test.describe('Force Majeure — Create & Redistribute', () => {
  test('GET /api/v1/force_majeure/ returns array', async ({ apiClient }) => {
    const month = currentMonth()
    const res = await apiClient.get(`/api/v1/force_majeure/?month=${month}`)
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()
  })

  test('POST /api/v1/force_majeure/ creates event', async ({ apiClient, cleanup }) => {
    const month = currentMonth(6)
    const [year, m] = month.split('-')
    const eventDate = `${year}-${m}-10`
    const rep = await createRep(apiClient, `${cleanup.namespace}_force_majeure`, 'active', cleanup)
    const res = await apiClient.post('/api/v1/force_majeure/', {
      data: {
        type: 'illness',
        rep_id: rep.id,
        event_date: eventDate,
        description: 'E2E test force majeure',
      },
    })
    expect([200, 201]).toContain(res.status())
    const body = await res.json()
    expect(body).toHaveProperty('id')
    expect(body.rep_id).toBe(rep.id)
    if (typeof body.id === 'string') {
      cleanup.trackForceMajeure(body.id)
    }
  })

  test('force majeure modal opens on schedule page', async ({ page }) => {
    await page.goto('/schedule')
    await page.click('text=Форс-мажор')
    await expect(page.locator('[class*="modal"]').first()).toBeVisible({ timeout: 5_000 })
  })
})
