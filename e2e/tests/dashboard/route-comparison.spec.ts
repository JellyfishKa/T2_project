import type { Page, Route as PlaywrightRoute } from '@playwright/test'
import { test, expect } from '../../fixtures/base'

const routeId = 'route-compare-1'
const routeName = 'Демо маршрут сравнения'

const routeItem = {
  id: routeId,
  name: routeName,
  locations: ['loc-2', 'loc-1', 'loc-3'],
  total_distance_km: 18.4,
  total_time_hours: 2.1,
  total_cost_rub: 940,
  model_used: 'qwen',
  fallback_reason: null,
  has_comparison: true,
  created_at: '2026-04-22T09:00:00Z',
}

const routeDetails = {
  ...routeItem,
  locations_sequence: ['loc-2', 'loc-1', 'loc-3'],
  locations_data: [
    {
      id: 'loc-2',
      name: 'ТТ Север',
      lat: 54.195,
      lon: 45.17,
      address: 'ул. Северная, 8',
      time_window_start: '09:00',
      time_window_end: '18:00',
      category: 'B',
      city: 'Саранск',
      district: 'Ленинский',
    },
    {
      id: 'loc-1',
      name: 'ТТ Центр',
      lat: 54.1871,
      lon: 45.1749,
      address: 'ул. Советская, 35',
      time_window_start: '09:00',
      time_window_end: '18:00',
      category: 'A',
      city: 'Саранск',
      district: 'Ленинский',
    },
    {
      id: 'loc-3',
      name: 'ТТ Юг',
      lat: 54.176,
      lon: 45.183,
      address: 'ул. Южная, 12',
      time_window_start: '10:00',
      time_window_end: '19:00',
      category: 'C',
      city: 'Саранск',
      district: 'Пролетарский',
    },
  ],
  metrics: [
    {
      id: 'metric-compare-1',
      route_id: routeId,
      model: 'qwen',
      response_time_ms: 980,
      quality_score: 92.1,
      cost_rub: 12.4,
      timestamp: '2026-04-22T09:00:03Z',
    },
  ],
}

const routeComparison = {
  route_id: routeId,
  original: [
    {
      id: 'loc-1',
      name: 'ТТ Центр',
      lat: 54.1871,
      lon: 45.1749,
      order: 1,
      address: 'ул. Советская, 35',
      category: 'A',
    },
    {
      id: 'loc-2',
      name: 'ТТ Север',
      lat: 54.195,
      lon: 45.17,
      order: 2,
      address: 'ул. Северная, 8',
      category: 'B',
    },
    {
      id: 'loc-3',
      name: 'ТТ Юг',
      lat: 54.176,
      lon: 45.183,
      order: 3,
      address: 'ул. Южная, 12',
      category: 'C',
    },
  ],
  current: [
    {
      id: 'loc-2',
      name: 'ТТ Север',
      lat: 54.195,
      lon: 45.17,
      order: 1,
      address: 'ул. Северная, 8',
      category: 'B',
    },
    {
      id: 'loc-1',
      name: 'ТТ Центр',
      lat: 54.1871,
      lon: 45.1749,
      order: 2,
      address: 'ул. Советская, 35',
      category: 'A',
    },
    {
      id: 'loc-3',
      name: 'ТТ Юг',
      lat: 54.176,
      lon: 45.183,
      order: 3,
      address: 'ул. Южная, 12',
      category: 'C',
    },
  ],
  diff: {
    distance_delta_km: -4.6,
    time_delta_hours: -0.7,
    cost_delta_rub: -180,
    changed_stops_count: 2,
    improvement_percentage: 20.0,
  },
  model_used: 'qwen',
  created_at: '2026-04-22T09:00:00Z',
}

const metricsPayload = {
  metrics: [
    {
      id: 'metric-compare-1',
      route_id: routeId,
      model: 'qwen',
      response_time_ms: 980,
      quality_score: 92.1,
      cost_rub: 12.4,
      timestamp: '2026-04-22T09:00:03Z',
    },
    {
      id: 'metric-compare-2',
      route_id: 'route-other',
      model: 'llama',
      response_time_ms: 1200,
      quality_score: 88.7,
      cost_rub: 16.8,
      timestamp: '2026-04-22T08:58:00Z',
    },
  ],
}

const modelComparisonPayload = {
  models: [
    {
      name: 'qwen',
      avg_response_time_ms: 980,
      avg_quality_score: 0.92,
      total_cost_rub: 18,
      success_rate: 0.99,
      usage_count: 24,
    },
    {
      name: 'llama',
      avg_response_time_ms: 1400,
      avg_quality_score: 0.9,
      total_cost_rub: 22,
      success_rate: 0.97,
      usage_count: 12,
    },
  ],
  recommendations: [
    {
      scenario: 'Короткие перестроения',
      recommended_model: 'qwen',
      reason: 'Быстрее отвечает для ежедневной оптимизации',
    },
  ],
}

const healthPayload = {
  status: 'healthy',
  database: 'connected',
  services: {
    database: 'connected',
    qwen: 'loaded',
    llama: 'loaded',
  },
  disk_free_mb: 4096,
  visits_today: 11,
  version: '1.2.0',
}

async function fulfillJson(route: PlaywrightRoute, payload: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(payload),
  })
}

async function mockDashboardApi(page: Page) {
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const pathname = url.pathname

    if (request.method() === 'GET' && pathname === '/api/v1/routes') {
      await fulfillJson(route, { total: 1, items: [routeItem] })
      return
    }

    if (request.method() === 'GET' && pathname === `/api/v1/routes/${routeId}`) {
      await fulfillJson(route, routeDetails)
      return
    }

    if (request.method() === 'GET' && pathname === `/api/v1/routes/${routeId}/comparison`) {
      await fulfillJson(route, routeComparison)
      return
    }

    if (request.method() === 'GET' && pathname === '/api/v1/metrics') {
      await fulfillJson(route, metricsPayload)
      return
    }

    if (request.method() === 'GET' && pathname === '/api/v1/benchmark/compare') {
      await fulfillJson(route, modelComparisonPayload)
      return
    }

    if (request.method() === 'GET' && pathname === '/api/v1/health') {
      await fulfillJson(route, healthPayload)
      return
    }

    if (request.method() === 'POST' && pathname === '/api/v1/routing/preview') {
      const body = request.postDataJSON() as {
        points?: Array<{ lat: number; lon: number }>
      }
      const points = Array.isArray(body.points) ? body.points : []
      await fulfillJson(route, {
        geometry: points.map((point) => [point.lat, point.lon]),
        distance_km: points.length >= 2 ? 18.4 : 0,
        time_minutes: points.length >= 2 ? 126 : 0,
        cost_rub: points.length >= 2 ? 940 : 0,
        traffic_lights_count: Math.max(points.length - 1, 0),
        source: 'road_network',
        transport_mode: 'car',
      })
      return
    }

    await route.continue()
  })
}

test.describe('Dashboard — Route Comparison', () => {
  test('opens shared compare modal and renders route summary with two route layers', async ({ page }) => {
    await mockDashboardApi(page)

    await page.goto('/dashboard')

    await expect(page.getByRole('heading', { name: 'Дашборд' })).toBeVisible({ timeout: 15_000 })

    const compareButton = page.getByRole('button', { name: `Сравнить маршрут ${routeName}` })
    await expect(compareButton).toBeVisible()
    await compareButton.click()

    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    await expect(dialog.getByRole('heading', { name: 'Сравнение маршрута' })).toBeVisible()
    await expect(dialog).toContainText('До оптимизации')
    await expect(dialog).toContainText('После оптимизации')
    await expect(dialog).toContainText('−4.6 км')
    await expect(dialog).toContainText('−0.7 ч')
    await expect(dialog).toContainText('−180 ₽')
    await expect(dialog).toContainText('Изменено точек')
    await expect(dialog).toContainText('20.0%')
    await expect(dialog).toContainText('↑1')
    await expect(dialog).toContainText('↓1')

    const polylines = dialog.locator('.leaflet-overlay-pane path.leaflet-interactive')
    await expect
      .poll(async () => await polylines.count(), { timeout: 15_000 })
      .toBeGreaterThanOrEqual(2)
  })
})
