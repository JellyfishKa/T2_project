import { test, expect } from '../../fixtures/base'
import { createLocation } from '../../fixtures/test-data'

test.describe('Smoke — API Regressions', () => {
  test('GET /api/v1/benchmark/compare returns comparison payload', async ({ apiClient }) => {
    const res = await apiClient.get('/api/v1/benchmark/compare')
    expect(res.status()).toBe(200)

    const body = await res.json()
    expect(body).toHaveProperty('models')
    expect(body).toHaveProperty('recommendations')
    expect(Array.isArray(body.models)).toBeTruthy()
    expect(Array.isArray(body.recommendations)).toBeTruthy()
  })

  test('POST /api/v1/routing/preview returns route geometry, travel time and cost', async ({ apiClient }) => {
    const res = await apiClient.post('/api/v1/routing/preview', {
      data: {
        points: [
          { lat: 54.203982, lon: 45.086872 },
          { lat: 54.15834, lon: 45.197896 },
        ],
      },
    })

    expect(res.status()).toBe(200)
    const body = await res.json()

    expect(Array.isArray(body.geometry)).toBeTruthy()
    expect(body.geometry.length).toBeGreaterThanOrEqual(2)
    expect(body.distance_km).toBeGreaterThan(0)
    expect(body.time_minutes).toBeGreaterThan(0)
    expect(body.cost_rub).toBeGreaterThan(0)
    expect(['road_network', 'fallback']).toContain(body.source)
  })

  test('POST /api/v1/optimize/variants returns variants with route metrics', async ({ apiClient, cleanup }) => {
    test.setTimeout(90_000)

    const healthRes = await apiClient.get('/api/v1/health')
    if (healthRes.status() === 200) {
      const health = await healthRes.json()
      if (health.llm_status !== 'loaded') {
        test.skip(true, `LLM not loaded (status: ${health.llm_status})`)
        return
      }
    }

    const firstLocation = await createLocation(apiClient, `${cleanup.namespace}_optimize_a`, 'C', cleanup)
    const secondLocation = await createLocation(apiClient, `${cleanup.namespace}_optimize_b`, 'C', cleanup)
    const res = await apiClient.post('/api/v1/optimize/variants', {
      data: {
        location_ids: [firstLocation.id, secondLocation.id],
        model: 'qwen',
        constraints: {},
      },
    })

    expect(res.status()).toBe(200)
    const body = await res.json()

    expect(Array.isArray(body.variants)).toBeTruthy()
    expect(body.variants.length).toBeGreaterThan(0)
    expect(body.variants[0].metrics.distance_km).toBeGreaterThanOrEqual(0)
    expect(body.variants[0].metrics.time_hours).toBeGreaterThan(0)
    expect(body.variants[0].metrics.cost_rub).toBeGreaterThanOrEqual(0)
  })
})
