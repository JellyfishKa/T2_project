import { mount, flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi, beforeEach } from 'vitest'

const { fetchRoutePreviewMock } = vi.hoisted(() => ({
  fetchRoutePreviewMock: vi.fn(),
}))

vi.mock('@/services/api', () => ({
  fetchRoutePreview: fetchRoutePreviewMock,
}))

vi.mock('leaflet', () => {
  const createMapInstance = () => ({
    setView: vi.fn().mockReturnThis(),
    remove: vi.fn(),
    fitBounds: vi.fn(),
    removeLayer: vi.fn(),
  })

  return {
    default: {
      Icon: {
        Default: {
          mergeOptions: vi.fn(),
        },
      },
      divIcon: vi.fn(() => ({})),
      marker: vi.fn(() => ({
        bindTooltip: vi.fn().mockReturnThis(),
      })),
      polyline: vi.fn(() => ({
        on: vi.fn().mockReturnThis(),
      })),
      featureGroup: vi.fn(() => ({
        addTo: vi.fn().mockReturnThis(),
        getBounds: vi.fn(() => ({})),
      })),
      map: vi.fn(() => createMapInstance()),
      tileLayer: vi.fn(() => ({
        addTo: vi.fn().mockReturnThis(),
      })),
    },
  }
})

import RouteMap from '@/components/RouteMap.vue'

describe('RouteMap.vue', () => {
  beforeEach(() => {
    fetchRoutePreviewMock.mockReset()
    fetchRoutePreviewMock.mockResolvedValue({
      geometry: [
        [55.7558, 37.6173],
        [55.7489, 37.616],
      ],
      distance_km: 12.5,
      time_minutes: 34,
      cost_rub: 500,
      traffic_lights_count: 4,
      source: 'road_network',
      transport_mode: 'car',
    })
  })

  it('does not reuse route preview cache across unmount/remount', async () => {
    const points = [
      { id: 'loc-1', name: 'Store 1', lat: 55.7558, lon: 37.6173, order: 1 },
      { id: 'loc-2', name: 'Store 2', lat: 55.7489, lon: 37.616, order: 2 },
    ]

    const firstWrapper = mount(RouteMap, {
      props: { points },
    })

    await flushPromises()
    firstWrapper.unmount()

    const secondWrapper = mount(RouteMap, {
      props: { points },
    })

    await flushPromises()
    secondWrapper.unmount()

    expect(fetchRoutePreviewMock).toHaveBeenCalledTimes(2)
  })
})
