import type { Page } from '@playwright/test'
import { test, expect } from '../../fixtures/base'
import { createRep, currentMonth, deleteRep, ensureGeneratedSchedule, RepData } from '../../fixtures/test-data'

const month = currentMonth(1)
const monthOffset = 1

let seedRep: RepData | null = null

async function openScheduleMonth(page: Page, offset: number) {
  await page.goto('/schedule')
  await page.waitForLoadState('networkidle')

  if (offset === 0) return

  const navigationButton = offset > 0 ? '▶' : '◀'
  for (let i = 0; i < Math.abs(offset); i++) {
    await page.getByRole('button', { name: navigationButton, exact: true }).click()
    await page.waitForLoadState('networkidle')
  }
}

test.describe('Schedule — Day Modal', () => {
  test.describe.configure({ mode: 'serial' })

  test.beforeEach(async ({ apiClient }) => {
    if (!seedRep) {
      seedRep = await createRep(apiClient, `E2E Schedule Day Modal ${Date.now()}`)
    }

    await ensureGeneratedSchedule(apiClient, month, [seedRep.id])
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

  test('clicking a day card opens day modal', async ({ page }) => {
    await openScheduleMonth(page, monthOffset)

    const card = page.locator('.schedule-view .card').filter({ hasText: /\d+\s*ТТ\s*·/ }).first()
    await expect(card).toBeVisible({ timeout: 8_000 })
    await card.locator('.cursor-pointer').first().click()

    await expect(page.locator('[class*="planner-modal"], [class*="modal"]').first()).toBeVisible({ timeout: 8_000 })
  })

  test('day modal shows transport mode selector', async ({ page }) => {
    await openScheduleMonth(page, monthOffset)

    const card = page.locator('.schedule-view .card').filter({ hasText: /\d+\s*ТТ\s*·/ }).first()
    await expect(card).toBeVisible({ timeout: 8_000 })
    await card.locator('.cursor-pointer').first().click()

    const modal = page.locator('[class*="planner-modal"], [class*="modal-overlay"]').first()
    await expect(modal).toBeVisible({ timeout: 8_000 })

    const transportSelect = modal.locator('select').first()
    await expect(transportSelect.locator('option[value="car"]')).toBeAttached()
    await expect(transportSelect.locator('option[value="taxi"]')).toBeAttached()
    await expect(transportSelect.locator('option[value="bus"]')).toBeAttached()
  })

  test('map links appear when route has multiple locations', async ({ page }) => {
    await openScheduleMonth(page, monthOffset)

    const cards = page.locator('.schedule-view .card').filter({ hasText: /\d+\s*ТТ\s*·/ })
    const count = await cards.count()
    if (count === 0) test.skip()

    for (let i = 0; i < count; i++) {
      const card = cards.nth(i)
      const text = await card.textContent()
      const match = text?.match(/(\d+)\s*ТТ/)
      if (match && parseInt(match[1]) >= 2) {
        await card.locator('.cursor-pointer').first().click()
        const modal = page.locator('[class*="planner-modal"]').first()
        await expect(modal).toBeVisible({ timeout: 8_000 })
        await page.waitForTimeout(2_000)
        await expect(modal.locator('text=Яндекс')).toBeVisible({ timeout: 8_000 })
        await expect(modal.locator('text=Google')).toBeVisible()
        await expect(modal.locator('text=2ГИС')).toBeVisible()
        return
      }
    }
    test.skip()
  })
})
