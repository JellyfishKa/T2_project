import { test, expect } from '../../fixtures/base'
import { currentMonth } from '../../fixtures/test-data'

test.describe('Export — Excel', () => {
  test('GET /api/v1/export/schedule returns xlsx content-type', async ({ apiClient }) => {
    const month = currentMonth()
    const res = await apiClient.get(`/api/v1/export/schedule?month=${month}`)
    expect(res.status()).toBe(200)
    const ct = res.headers()['content-type'] ?? ''
    expect(ct).toContain('spreadsheetml')
  })

  test('exported file is non-empty (> 1 KB)', async ({ apiClient }) => {
    const month = currentMonth()
    const res = await apiClient.get(`/api/v1/export/schedule?month=${month}`)
    expect(res.status()).toBe(200)
    const body = await res.body()
    expect(body.length).toBeGreaterThan(1024)
  })

  test('Content-Disposition header includes month in filename', async ({ apiClient }) => {
    const month = currentMonth()
    const res = await apiClient.get(`/api/v1/export/schedule?month=${month}`)
    expect(res.status()).toBe(200)
    const cd = res.headers()['content-disposition'] ?? ''
    expect(cd).toContain(month)
  })

  test('Excel download button visible on schedule page', async ({ page }) => {
    await page.goto('/schedule')
    await expect(page.locator('button:has-text("Excel"), button:has-text("Экспорт")')).toBeVisible()
  })

  test('clicking Excel button triggers file download', async ({ page }) => {
    await page.goto('/schedule')

    const downloadPromise = page.waitForEvent('download', { timeout: 15_000 })
    await page.locator('button:has-text("Excel")').click()
    const download = await downloadPromise

    expect(download.suggestedFilename()).toContain('.xlsx')
  })
})
