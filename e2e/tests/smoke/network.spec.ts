import type { Page } from '@playwright/test'
import { test, expect } from '../../fixtures/base'

const FRONTEND_ORIGIN = new URL(process.env.BASE_URL ?? 'http://localhost:80').origin
const API_ORIGIN = new URL(process.env.API_URL ?? 'http://localhost:8000/api/v1').origin

async function expectNoOwn4xx5xx(pagePath: string, page: Page) {
  const failures: string[] = []

  page.on('response', (response) => {
    const status = response.status()
    if (status < 400) return

    const url = response.url()
    const origin = new URL(url).origin
    if (origin !== FRONTEND_ORIGIN && origin !== API_ORIGIN) return
    if (url.endsWith('/favicon.ico')) return

    failures.push(`${status} ${url}`)
  })

  await page.goto(pagePath)
  if (pagePath === '/schedule') {
    await expect(page.getByRole('button', { name: 'Сгенерировать план' })).toBeVisible({ timeout: 15_000 })
  } else {
    await expect(page.locator('body')).toBeVisible({ timeout: 15_000 })
  }
  await page.waitForTimeout(4_000)

  expect(failures, `Unexpected 4xx/5xx requests on ${pagePath}: ${failures.join('\n')}`).toHaveLength(0)
}

test.describe('Smoke — Network Regressions', () => {
  test('dashboard has no own 4xx/5xx requests', async ({ page }) => {
    test.setTimeout(45_000)
    await expectNoOwn4xx5xx('/dashboard', page)
  })

  test('schedule has no own 4xx/5xx requests', async ({ page }) => {
    test.setTimeout(45_000)
    await expectNoOwn4xx5xx('/schedule', page)
  })
})
