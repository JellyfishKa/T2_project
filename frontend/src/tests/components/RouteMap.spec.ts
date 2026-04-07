import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'

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

vi.mock('leaflet', () => {
  const L = {
    map: vi.fn(() => fakeMap),
    tileLayer: vi.fn(() => ({ addTo: vi.fn() })),
    marker: vi.fn(() => fakeMarker),
    polyline: vi.fn(() => ({})),
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

import RouteMap from '@/components/RouteMap.vue'
import L from 'leaflet'

describe('RouteMap.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('mounts without errors when points is empty', () => {
    const wrapper = mount(RouteMap, { props: { points: [] } })
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

    expect(L.marker).toHaveBeenCalledTimes(3)
    expect(L.polyline).toHaveBeenCalledTimes(1)
    expect(L.featureGroup).toHaveBeenCalledTimes(1)
    expect(fakeMap.fitBounds).toHaveBeenCalledTimes(1)
    expect(fakeMarker.bindTooltip).toHaveBeenCalledTimes(3)

    wrapper.unmount()
  })

  it('skips points with non-finite coordinates', () => {
    const points = [
      { id: '1', name: 'A', lat: NaN, lon: 45.0, order: 1 },
      { id: '2', name: 'B', lat: 54.1, lon: 45.1, order: 2 },
    ]
    const wrapper = mount(RouteMap, { props: { points } })
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

    expect(L.marker).toHaveBeenCalledTimes(2)
    expect(L.polyline).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })
})
