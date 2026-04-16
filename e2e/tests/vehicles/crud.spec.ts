import { faker } from '@faker-js/faker/locale/ru'
import { test, expect } from '../../fixtures/base'
import { createVehicle, deleteVehicle } from '../../fixtures/test-data'

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

test.describe('Vehicles — CRUD', () => {
  test('create vehicle via UI → appears in table', async ({ page, apiClient }) => {
    const name = `Test_${faker.string.alphanumeric(6)}`

    await page.goto('/cars')
    // The add form is always visible — no toggle button needed
    await page.fill('input[placeholder="Lada Granta"]', name)
    await page.fill('input[placeholder="63"]', '55')
    await page.fill('input[placeholder="9.0"]', '11')
    await page.fill('input[placeholder="6.5"]', '8')
    await page.click('button:has-text("Добавить")')

    await expect(page.locator(`text=${name}`).first()).toBeVisible({ timeout: 10_000 })

    // cleanup
    const res = await apiClient.get('/api/v1/routing/')
    const vehicles = await res.json()
    const v = Array.isArray(vehicles) ? vehicles.find((x: { name: string }) => x.name === name) : null
    if (v) await deleteVehicle(apiClient, v.id)
  })

  test('delete vehicle → disappears from list', async ({ page, apiClient }) => {
    const name = `Test_${faker.string.alphanumeric(6)}`
    const vehicle = await createVehicle(apiClient, name)

    await page.goto('/cars')
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

    // cleanup in case UI delete failed
    await apiClient.delete(`/api/v1/routing/${vehicle.id}`).catch(() => {})
  })

  test('created vehicle appears in reps dropdown', async ({ page, apiClient }) => {
    const vname = `Test_${faker.string.alphanumeric(6)}`
    const vehicle = await createVehicle(apiClient, vname)

    await page.goto('/reps')
    await page.click('text=+ Добавить сотрудника')

    const vehicleSelect = page.locator('select').filter({ hasText: /Такси|Автобус/ }).first()
    await expect(vehicleSelect.locator(`option:has-text("${vname}")`)).toBeAttached({ timeout: 5_000 })

    await deleteVehicle(apiClient, vehicle.id)
  })

  test('GET /api/v1/routing/ returns list', async ({ apiClient }) => {
    const res = await apiClient.get('/api/v1/routing/')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()
  })
})
