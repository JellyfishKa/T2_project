import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

// Stub leaflet image asset imports (Vite handles these in the real build,
// but Vitest+jsdom does not transform PNGs).
vi.mock('leaflet/dist/images/marker-icon.png', () => ({ default: 'icon.png' }))
vi.mock('leaflet/dist/images/marker-icon-2x.png', () => ({ default: 'icon-2x.png' }))
vi.mock('leaflet/dist/images/marker-shadow.png', () => ({ default: 'shadow.png' }))

// Fake Leaflet — jsdom has no layout, so a real L.map() throws.
const fakeMap = {
  setView: vi.fn().mockReturnThis(),
  addLayer: vi.fn(),
  removeLayer: vi.fn(),
  remove: vi.fn(),
  fitBounds: vi.fn(),
}

const fakeFeatureGroup = {
  addTo: vi.fn().mockReturnThis(),
  getBounds: vi.fn().mockReturnValue({}),
}

const fakeMarker = {
  bindTooltip: vi.fn().mockReturnThis(),
}

const fakePolyline = {
  on: vi.fn().mockReturnThis(),
  bindTooltip: vi.fn().mockReturnThis(),
}

vi.mock('leaflet', () => {
  const L = {
    map: vi.fn(() => fakeMap),
    tileLayer: vi.fn(() => ({ addTo: vi.fn() })),
    marker: vi.fn(() => fakeMarker),
    polyline: vi.fn(() => fakePolyline),
    featureGroup: vi.fn(() => fakeFeatureGroup),
    divIcon: vi.fn(() => ({})),
    Icon: {
      Default: {
        mergeOptions: vi.fn(),
      },
    },
  }
  return { default: L, ...L }
})

vi.mock('@/services/api', () => ({
  fetchRoutePreview: vi.fn(async (points: Array<{ lat: number; lon: number }>) => ({
    geometry: points.map((point) => [point.lat, point.lon] as [number, number]),
    distance_km: 10,
    time_minutes: 25,
    cost_rub: 70,
    traffic_lights_count: 3,
    source: 'road_network',
  })),
}))

import RouteMap from '@/components/RouteMap.vue'
import L from 'leaflet'

describe('RouteMap.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('mounts without errors when points is empty', async () => {
    const wrapper = mount(RouteMap, { props: { points: [] } })
    await flushPromises()
    expect(wrapper.exists()).toBe(true)
    expect(L.map).toHaveBeenCalledTimes(1)
    // No fitBounds when no points
    expect(fakeMap.fitBounds).not.toHaveBeenCalled()
    wrapper.unmount()
    expect(fakeMap.remove).toHaveBeenCalled()
  })

  it('renders markers, polyline and fits bounds for 3 points', async () => {
    const points = [
      { id: '1', name: 'A', address: 'addr A', lat: 54.0, lon: 45.0, order: 1 },
      { id: '2', name: 'B', address: null,    lat: 54.1, lon: 45.1, order: 2 },
      { id: '3', name: 'C', address: 'addr C', lat: 54.2, lon: 45.2, order: 3 },
    ]
    const wrapper = mount(RouteMap, { props: { points } })
    await flushPromises()

    expect(L.marker).toHaveBeenCalledTimes(3)
    expect(L.polyline).toHaveBeenCalledTimes(1)
    expect(L.featureGroup).toHaveBeenCalledTimes(1)
    expect(fakeMap.fitBounds).toHaveBeenCalledTimes(1)
    expect(fakeMarker.bindTooltip).toHaveBeenCalledTimes(3)

    wrapper.unmount()
  })

  it('skips points with non-finite coordinates', async () => {
    const points = [
      { id: '1', name: 'A', lat: NaN, lon: 45.0, order: 1 },
      { id: '2', name: 'B', lat: 54.1, lon: 45.1, order: 2 },
    ]
    const wrapper = mount(RouteMap, { props: { points } })
    await flushPromises()
    expect(L.marker).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('re-renders when points prop changes', async () => {
    const wrapper = mount(RouteMap, { props: { points: [] } })
    expect(L.marker).not.toHaveBeenCalled()

    await wrapper.setProps({
      points: [
        { id: '1', name: 'A', lat: 54.0, lon: 45.0, order: 1 },
        { id: '2', name: 'B', lat: 54.1, lon: 45.1, order: 2 },
      ],
    })
    await flushPromises()

    expect(L.marker).toHaveBeenCalledTimes(2)
    expect(L.polyline).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('multi-route mode draws one polyline per route and markers only for selected', async () => {
    const routes = [
      {
        id: 1,
        color: '#3b82f6',
        selected: false,
        points: [
          { id: 'a1', name: 'A1', lat: 54.0, lon: 45.0, order: 1 },
          { id: 'a2', name: 'A2', lat: 54.1, lon: 45.1, order: 2 },
        ],
      },
      {
        id: 2,
        color: '#10b981',
        selected: true,
        points: [
          { id: 'b1', name: 'B1', lat: 54.2, lon: 45.0, order: 1 },
          { id: 'b2', name: 'B2', lat: 54.3, lon: 45.1, order: 2 },
          { id: 'b3', name: 'B3', lat: 54.4, lon: 45.2, order: 3 },
        ],
      },
      {
        id: 3,
        color: '#8b5cf6',
        selected: false,
        points: [
          { id: 'c1', name: 'C1', lat: 54.5, lon: 45.3, order: 1 },
          { id: 'c2', name: 'C2', lat: 54.6, lon: 45.4, order: 2 },
        ],
      },
    ]
    const wrapper = mount(RouteMap, { props: { routes } })
    await flushPromises()

    expect(L.polyline).toHaveBeenCalledTimes(3)
    // Markers only for the selected variant (variant 2 → 3 points)
    expect(L.marker).toHaveBeenCalledTimes(3)
    expect(fakeMap.fitBounds).toHaveBeenCalledTimes(1)

    wrapper.unmount()
  })
})
