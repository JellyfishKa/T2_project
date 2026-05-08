import { test, expect } from '../../fixtures/base'

test.describe('Smoke — policy benchmark endpoints', () => {
  test('POST /api/v1/benchmark/policy/run is either forbidden or accepted', async ({ apiClient }) => {
    const res = await apiClient.post('/api/v1/benchmark/policy/run')
    expect([202, 403]).toContain(res.status())
  })

  test('GET /api/v1/benchmark/policy/recommendation returns json or not-found', async ({ apiClient }) => {
    const res = await apiClient.get('/api/v1/benchmark/policy/recommendation')
    expect([200, 404]).toContain(res.status())
    if (res.status() === 200) {
      const body = await res.json()
      expect(body).toHaveProperty('recommended_policy')
    }
  })
})
