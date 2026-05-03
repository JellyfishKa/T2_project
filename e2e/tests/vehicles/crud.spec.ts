import { faker } from '@faker-js/faker/locale/ru'
import { test, expect } from '../../fixtures/base'
import { createVehicle } from '../../fixtures/test-data'

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

test.describe('Vehicles — CRUD', () => {
  test('create vehicle via UI → appears in table', async ({ page, apiClient, cleanup }) => {
    const name = `Test_${faker.string.alphanumeric(6)}`

    await page.goto('/database?tab=vehicles')
    // The add form is always visible — no toggle button needed
    await page.fill('input[placeholder="Lada Granta"]', name)
    await page.fill('input[placeholder="63"]', '55')
    await page.fill('input[placeholder="9.0"]', '11')
    await page.fill('input[placeholder="6.5"]', '8')
    await page.click('button:has-text("Добавить")')

    await expect(page.locator(`text=${name}`).first()).toBeVisible({ timeout: 10_000 })

    const res = await apiClient.get('/api/v1/routing/')
    const vehicles = await res.json()
    const vehicle = Array.isArray(vehicles) ? vehicles.find((x: { id: string; name: string }) => x.name === name) : null
    if (vehicle) cleanup.trackVehicle(vehicle.id)
  })

  test('delete vehicle → disappears from list', async ({ page, apiClient, cleanup }) => {
    const name = `Test_${faker.string.alphanumeric(6)}`
    await createVehicle(apiClient, name, 50, 10, 7, cleanup)

    await page.goto('/database?tab=vehicles')
    const row = page
      .locator('tbody tr')
      .filter({ has: page.getByRole('cell', { name, exact: true }) })
      .first()
    await expect(row).toBeVisible()

    const handler = async (d: any) => d.accept()
    page.on('dialog', handler)
    await row.getByRole('button', { name: 'Удалить' }).click()
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {})
    page.off('dialog', handler)

    await expect(page.getByRole('cell', { name: new RegExp(`^${escapeRegex(name)}$`) })).toHaveCount(0, { timeout: 10_000 })
  })

  test('created vehicle appears in employees dropdown', async ({ page, apiClient, cleanup }) => {
    const vname = `Test_${faker.string.alphanumeric(6)}`
    await createVehicle(apiClient, vname, 50, 10, 7, cleanup)

    await page.goto('/database?tab=employees')
    await page.click('text=+ Добавить сотрудника')

    const vehicleSelect = page.locator('[data-testid="new-rep-vehicle-select-db"]')
    await expect(vehicleSelect.locator(`option:has-text("${vname}")`)).toBeAttached({ timeout: 5_000 })
  })

  test('GET /api/v1/routing/ returns list', async ({ apiClient }) => {
    const res = await apiClient.get('/api/v1/routing/')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()
  })
})
