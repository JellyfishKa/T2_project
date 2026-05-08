import { test, expect } from '../../fixtures/base'
import { createRep, currentMonth } from '../../fixtures/test-data'

test.describe('Schedule — generate optimized', () => {
  test('POST /api/v1/schedule/generate-optimized returns completed payload for small dataset', async ({ apiClient, cleanup }) => {
    const rep1 = await createRep(apiClient, `${cleanup.namespace}_rep1`, 'active', cleanup)
    const rep2 = await createRep(apiClient, `${cleanup.namespace}_rep2`, 'active', cleanup)

    const month = `${currentMonth()}-01`
    const res = await apiClient.post('/api/v1/schedule/generate-optimized', {
      data: {
        month,
        reps: [rep1.id, rep2.id],
        trade_points: [
          { id: `${cleanup.namespace}_tp1`, category: 'A', latitude: 54.18, longitude: 45.17 },
          { id: `${cleanup.namespace}_tp2`, category: 'B', latitude: 54.2, longitude: 45.2 },
          { id: `${cleanup.namespace}_tp3`, category: 'C', latitude: 54.22, longitude: 45.15 },
        ],
        async_mode: false,
        force: true,
        max_visits_per_day: 2,
        policy_mode: 'algorithm_primary',
        llm_fallback_model: 'llama',
      },
    })

    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.status).toBe('completed')
    expect(body.total_distance_km).toBeGreaterThanOrEqual(0)
    expect(Array.isArray(body.days)).toBeTruthy()
    expect(body.meta.policy_mode).toBe('algorithm_primary')
    expect(body.meta.llm_fallback_model).toBe('llama')
  })
})
