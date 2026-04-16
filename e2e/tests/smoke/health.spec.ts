import { test, expect } from '../../fixtures/base'
import { rootApiUrl } from '../../fixtures/test-data'

const PAGES = ['/', '/dashboard', '/reps', '/cars', '/schedule', '/analytics', '/optimize']

test.describe('Smoke — Health & Page Loads', () => {
  test('API /health returns status=healthy', async ({ apiClient }) => {
    const res = await apiClient.get(rootApiUrl('/health'))
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.status).toBe('healthy')
  })


  for (const route of PAGES) {
    test(`Page ${route} loads without JS errors`, async ({ page }) => {
      const errors: string[] = []
      // Only catch actual JS exceptions, not API console.error logs
      page.on('pageerror', (err) => errors.push(err.message))

      await page.goto(route)
      await page.waitForLoadState('networkidle')

      expect(errors, `JS exceptions on ${route}: ${errors.join(', ')}`).toHaveLength(0)
    })
  }
})
