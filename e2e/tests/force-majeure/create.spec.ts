import { test, expect } from '../../fixtures/base'
import { currentMonth } from '../../fixtures/test-data'

test.describe('Force Majeure — Create & Redistribute', () => {
  test('GET /api/v1/force_majeure/ returns array', async ({ apiClient }) => {
    const month = currentMonth()
    const res = await apiClient.get(`/api/v1/force_majeure/?month=${month}`)
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()
  })

  test('POST /api/v1/force_majeure/ creates event', async ({ apiClient }) => {
    const month = currentMonth()
    const [year, m] = month.split('-')
    const eventDate = `${year}-${m}-10`

    const repsRes = await apiClient.get('/api/v1/reps/')
    const reps = await repsRes.json()
    if (!Array.isArray(reps) || !reps.length) return test.skip()

    const repId = reps[0].id
    const res = await apiClient.post('/api/v1/force_majeure/', {
      data: {
        type: 'illness',
        rep_id: repId,
        event_date: eventDate,
        description: 'E2E test force majeure',
      },
    })
    expect([200, 201]).toContain(res.status())
    const body = await res.json()
    expect(body).toHaveProperty('id')
    expect(body.rep_id).toBe(repId)
  })

  test('force majeure modal opens on schedule page', async ({ page }) => {
    await page.goto('/schedule')
    await page.click('text=Форс-мажор')
    await expect(page.locator('[class*="modal"]').first()).toBeVisible({ timeout: 5_000 })
  })
})
