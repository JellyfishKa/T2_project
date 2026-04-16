import type { APIRequestContext, Locator, Page } from '@playwright/test'
import { test, expect } from '../../fixtures/base'
import { createRep, currentMonth, deleteRep, ensureGeneratedSchedule, RepData } from '../../fixtures/test-data'

const month = currentMonth(1)

let seedRep: RepData | null = null

const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

function monthLabelFor(monthValue: string) {
  const [year, monthNumber] = monthValue.split('-').map(Number)
  return `${monthNames[monthNumber - 1]} ${year}`
}

function parseMonthLabel(label: string) {
  const [monthName, yearRaw] = label.trim().split(/\s+/)
  const monthIndex = monthNames.indexOf(monthName)
  return {
    year: Number(yearRaw),
    month: monthIndex + 1,
  }
}

async function openScheduleMonth(page: Page, targetMonth: string) {
  await page.goto('/schedule')
  await expect(page.getByRole('button', { name: 'Сгенерировать план' })).toBeVisible({ timeout: 15_000 })

  const targetLabel = monthLabelFor(targetMonth)
  const monthChip = page.locator('span').filter({ hasText: /^(Январь|Февраль|Март|Апрель|Май|Июнь|Июль|Август|Сентябрь|Октябрь|Ноябрь|Декабрь)\s+\d{4}$/ }).first()

  for (let i = 0; i < 24; i++) {
    const currentLabel = ((await monthChip.textContent()) ?? '').trim()
    if (currentLabel === targetLabel) return

    const current = parseMonthLabel(currentLabel)
    const target = parseMonthLabel(targetLabel)
    const currentKey = current.year * 12 + current.month
    const targetKey = target.year * 12 + target.month
    const navigationButton = targetKey > currentKey ? '▶' : '◀'

    await page.getByRole('button', { name: navigationButton, exact: true }).click()
    await page.waitForTimeout(1_000)
  }

  throw new Error(`Could not navigate schedule page to ${targetLabel}`)
}

async function openDayModalWithMinLocations(
  page: Page,
  apiClient: APIRequestContext,
  minLocations: number,
) {
  await openScheduleMonth(page, month)

  const res = await apiClient.get(`/api/v1/schedule/?month=${month}`)
  expect(res.status()).toBe(200)
  const body = await res.json()

  const targetRoute = (body.routes as Array<{ date: string; rep_name: string; total_tt: number }>).find(
    (route) => route.total_tt >= minLocations,
  )
  if (!targetRoute) return null

  const card = page
    .locator('.schedule-view .card')
    .filter({ hasText: targetRoute.date })
    .filter({ hasText: targetRoute.rep_name })
    .first()

  await expect(card).toBeVisible({ timeout: 15_000 })
  await card.locator('.cursor-pointer').first().click()

  const modal = page.locator('.planner-modal').first()
  await expect(modal).toBeVisible({ timeout: 8_000 })
  return modal

}

function parseCost(metrics: string | null): number | null {
  if (!metrics) return null
  const match = metrics.match(/(\d+(?:[.,]\d+)?)\s*₽/)
  if (!match) return null
  return Number(match[1].replace(',', '.'))
}

async function waitForMetricsTextChange(page: Page, locatorText: Locator, previous: string) {
  for (let attempt = 0; attempt < 16; attempt++) {
    const current = (await locatorText.textContent())?.trim() ?? ''
    if (current && current !== previous) {
      return current
    }
    await page.waitForTimeout(500)
  }

  throw new Error(`Route metrics did not change from "${previous}"`)
}

test.describe('Schedule — Day Modal', () => {
  test.describe.configure({ mode: 'serial' })
  test.setTimeout(90_000)

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

  test('clicking a day card opens day modal', async ({ page, apiClient }) => {
    const modal = await openDayModalWithMinLocations(page, apiClient, 1)
    expect(modal).not.toBeNull()
  })

  test('day modal shows transport mode selector', async ({ page, apiClient }) => {
    const modal = await openDayModalWithMinLocations(page, apiClient, 1)
    expect(modal).not.toBeNull()
    if (!modal) return

    const transportSelect = modal.locator('select').first()
    await expect(transportSelect.locator('option[value="car"]')).toBeAttached()
    await expect(transportSelect.locator('option[value="taxi"]')).toBeAttached()
    await expect(transportSelect.locator('option[value="bus"]')).toBeAttached()
  })

  test('map links appear when route has multiple locations', async ({ page, apiClient }) => {
    const modal = await openDayModalWithMinLocations(page, apiClient, 2)
    if (!modal) test.skip()
    if (!modal) return

    await page.waitForTimeout(2_000)
    await expect(modal.locator('text=Яндекс')).toBeVisible({ timeout: 8_000 })
    await expect(modal.locator('text=Google')).toBeVisible()
    await expect(modal.locator('text=2ГИС')).toBeVisible()

    await expect(modal.locator('a:has-text("Яндекс")')).toHaveAttribute('href', /yandex\.ru/)
    await expect(modal.locator('a:has-text("Google")')).toHaveAttribute('href', /google\.com/)
    await expect(modal.locator('a:has-text("2ГИС")')).toHaveAttribute('href', /2gis\.ru/)
  })

  test('day modal shows route metrics with distance, time and cost', async ({ page, apiClient }) => {
    const modal = await openDayModalWithMinLocations(page, apiClient, 2)
    if (!modal) test.skip()
    if (!modal) return

    const activeRouteMetrics = modal.locator('.planner-summary-card').first().locator('.planner-summary-card__hint')
    await expect(activeRouteMetrics).toContainText('км')
    await expect(activeRouteMetrics).toContainText('ч')
    await expect(activeRouteMetrics).toContainText('₽')
  })

  test('changing transport mode recalculates route metrics', async ({ page, apiClient }) => {
    const modal = await openDayModalWithMinLocations(page, apiClient, 2)
    if (!modal) test.skip()
    if (!modal) return

    const transportSelect = modal.locator('select').first()
    const activeRouteMetrics = modal.locator('.planner-summary-card').first().locator('.planner-summary-card__hint')

    await expect(activeRouteMetrics).toContainText('₽', { timeout: 10_000 })
    const initialMetrics = ((await activeRouteMetrics.textContent()) ?? '').trim()
    expect(parseCost(initialMetrics)).not.toBeNull()

    const currentMode = await transportSelect.inputValue()
    const firstAlternative = ['car', 'taxi', 'bus'].find((mode) => mode !== currentMode)
    const secondAlternative = ['car', 'taxi', 'bus'].find(
      (mode) => mode !== currentMode && mode !== firstAlternative,
    )

    if (!firstAlternative || !secondAlternative) {
      throw new Error(`Could not find alternative transport modes for "${currentMode}"`)
    }

    await transportSelect.selectOption(firstAlternative)
    const firstChangedMetrics = await waitForMetricsTextChange(page, activeRouteMetrics, initialMetrics)
    expect(parseCost(firstChangedMetrics)).not.toBeNull()

    await transportSelect.selectOption(secondAlternative)
    const secondChangedMetrics = await waitForMetricsTextChange(page, activeRouteMetrics, firstChangedMetrics)
    expect(parseCost(secondChangedMetrics)).not.toBeNull()

    expect(firstChangedMetrics).not.toBe(initialMetrics)
    expect(secondChangedMetrics).not.toBe(firstChangedMetrics)
  })
})
