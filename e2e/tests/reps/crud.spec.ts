import { faker } from '@faker-js/faker/locale/ru'
import { test, expect } from '../../fixtures/base'
import { createRep, deleteRep } from '../../fixtures/test-data'

function uniqueRepName(): string {
  return `E2E_${faker.person.firstName()}_${faker.string.alphanumeric(6)}`
}

test.describe('Reps — CRUD', () => {
  test('create rep via UI → appears in list', async ({ page, apiClient }) => {
    const name = uniqueRepName()

    await page.goto('/reps')
    await page.click('text=+ Добавить сотрудника')
    await page.fill('input[placeholder*="Иванов"]', name)
    await page.click('button:has-text("Сохранить")')

    await expect(page.locator('.card').filter({ has: page.locator('.font-medium', { hasText: name }) }).first()).toBeVisible({ timeout: 10_000 })

    // cleanup
    const res = await apiClient.get('/api/v1/reps/')
    const reps = await res.json()
    const rep = Array.isArray(reps) ? reps.find((r: { name: string }) => r.name === name) : null
    if (rep) await deleteRep(apiClient, rep.id)
  })

  test('change rep status via dropdown', async ({ page, apiClient }) => {
    const name = uniqueRepName()
    const rep = await createRep(apiClient, name)

    await page.goto('/reps')
    const repCard = page.locator('.card').filter({
      has: page.locator('.font-medium', { hasText: name }),
    }).first()
    await expect(repCard).toBeVisible()

    await repCard.locator('select').first().selectOption('sick')

    await expect(repCard.locator('text=Больничный')).toBeVisible({ timeout: 5_000 })

    await deleteRep(apiClient, rep.id)
  })

  test('delete rep → disappears from list', async ({ page, apiClient }) => {
    const name = uniqueRepName()
    const rep = await createRep(apiClient, name)

    await page.goto('/reps')
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

    // cleanup in case UI delete failed
    await apiClient.delete(`/api/v1/reps/${rep.id}`).catch(() => {})
  })

  test('create rep via API → appears on /reps page', async ({ page, apiClient }) => {
    const name = uniqueRepName()
    const rep = await createRep(apiClient, name)

    await page.goto('/reps')
    await expect(page.locator('.card').filter({ has: page.locator('.font-medium', { hasText: name }) }).first()).toBeVisible()

    await deleteRep(apiClient, rep.id)
  })
})
