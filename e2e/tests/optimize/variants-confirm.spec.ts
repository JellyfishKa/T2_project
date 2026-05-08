import { test, expect } from '../../fixtures/base'
import { createLocation } from '../../fixtures/test-data'

test.describe('Optimize — variants and confirm flow', () => {
  test('POST /api/v1/optimize/variants returns ranked alternatives and /confirm saves selected', async ({ apiClient, cleanup }) => {
    const locA = await createLocation(apiClient, `${cleanup.namespace}_va`, 'A', cleanup)
    const locB = await createLocation(apiClient, `${cleanup.namespace}_vb`, 'B', cleanup)
    const locC = await createLocation(apiClient, `${cleanup.namespace}_vc`, 'C', cleanup)

    const variantsRes = await apiClient.post('/api/v1/optimize/variants', {
      data: {
        location_ids: [locA.id, locB.id, locC.id],
        model: 'llama',
        policy_mode: 'algorithm_primary',
        max_alternatives: 3,
        constraints: {},
      },
    })
    expect(variantsRes.status()).toBe(200)
    const variantsBody = await variantsRes.json()

    expect(Array.isArray(variantsBody.variants)).toBeTruthy()
    expect(variantsBody.variants.length).toBeGreaterThan(0)
    expect(variantsBody.variants[0].is_recommended).toBeTruthy()
    expect(variantsBody.variants[0].rank).toBe(1)

    const selected = variantsBody.variants[0]
    const confirmRes = await apiClient.post('/api/v1/optimize/confirm', {
      data: {
        name: `E2E selected ${cleanup.namespace}`,
        locations: selected.locations,
        total_distance_km: selected.metrics.distance_km,
        total_time_hours: selected.metrics.time_hours,
        total_cost_rub: selected.metrics.cost_rub,
        quality_score: selected.metrics.quality_score,
        model_used: selected.algorithm,
        original_location_ids: [locA.id, locB.id, locC.id],
        original_total_distance_km: selected.metrics.distance_km,
        original_total_time_hours: selected.metrics.time_hours,
        original_total_cost_rub: selected.metrics.cost_rub,
      },
    })
    expect(confirmRes.status()).toBe(200)
    const confirmBody = await confirmRes.json()
    expect(confirmBody.id).toBeTruthy()
    expect(confirmBody.model_used).toBe(selected.algorithm)
    expect(confirmBody.locations.length).toBe(3)
  })

  test('POST /api/v1/optimize/variants with one location returns 422', async ({ apiClient, cleanup }) => {
    const loc = await createLocation(apiClient, `${cleanup.namespace}_single`, 'C', cleanup)
    const res = await apiClient.post('/api/v1/optimize/variants', {
      data: {
        location_ids: [loc.id],
        model: 'qwen',
        constraints: {},
      },
    })
    expect(res.status()).toBe(422)
  })
})
