import { faker } from '@faker-js/faker/locale/ru'
import { test, expect } from '../../fixtures/base'
import { createRep } from '../../fixtures/test-data'

function uniqueRepName(): string {
  return `E2E_${faker.person.firstName()}_${faker.string.alphanumeric(6)}`
}

test.describe('Reps — CRUD', () => {
  test('create rep via UI → appears in list', async ({ page, apiClient, cleanup }) => {
    const name = uniqueRepName()

    await page.goto('/database?tab=employees')
    await page.click('text=+ Добавить сотрудника')
    await page.fill('input[placeholder*="Иванов"]', name)
    await page.click('button:has-text("Сохранить")')

    await expect(page.locator('.card').filter({ has: page.locator('.font-medium', { hasText: name }) }).first()).toBeVisible({ timeout: 10_000 })

    const res = await apiClient.get('/api/v1/reps/')
    const reps = await res.json()
    const rep = Array.isArray(reps) ? reps.find((r: { id: string; name: string }) => r.name === name) : null
    if (rep) cleanup.trackRep(rep.id)
  })

  test('change rep status via dropdown', async ({ page, apiClient, cleanup }) => {
    const name = uniqueRepName()
    await createRep(apiClient, name, 'active', cleanup)

    await page.goto('/database?tab=employees')
    const repCard = page.locator('.card').filter({
      has: page.locator('.font-medium', { hasText: name }),
    }).first()
    await expect(repCard).toBeVisible()

    const statusSelect = repCard.locator('select').first()
    await statusSelect.selectOption('sick')
    await expect(statusSelect).toHaveValue('sick')
  })

  test('delete rep → disappears from list', async ({ page, apiClient, cleanup }) => {
    const name = uniqueRepName()
    await createRep(apiClient, name, 'active', cleanup)

    await page.goto('/database?tab=employees')
    const repCard = page.locator('.card').filter({
      has: page.locator('.font-medium', { hasText: name }),
    }).first()
    await expect(repCard).toBeVisible()

    const handler = async (d: any) => d.accept()
    page.on('dialog', handler)
    await repCard.getByRole('button', { name: 'Удалить' }).click()
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {})
    page.off('dialog', handler)

    await expect(page.locator('.card').filter({
      has: page.locator('.font-medium', { hasText: name }),
    })).toHaveCount(0, { timeout: 10_000 })
  })

  test('create rep via API → appears on database employees page', async ({ page, apiClient, cleanup }) => {
    const name = uniqueRepName()
    await createRep(apiClient, name, 'active', cleanup)

    await page.goto('/database?tab=employees')
    await expect(page.locator('.card').filter({ has: page.locator('.font-medium', { hasText: name }) }).first()).toBeVisible()
  })
})
