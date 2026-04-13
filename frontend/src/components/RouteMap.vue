<template>
  <div class="route-map-wrapper border rounded-lg overflow-hidden" :style="{ height: height ?? '24rem' }">
    <div ref="mapEl" class="route-map-container" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import L from 'leaflet'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'
import { fetchRoutePreview } from '@/services/api'

export interface RoutePoint {
  id: string
  name: string
  address?: string | null
  lat: number
  lon: number
  order: number
  color?: string
}

export interface RouteSet {
  id: string | number
  color: string
  points: RoutePoint[]
  selected?: boolean
}

const props = defineProps<{
  points?: RoutePoint[]
  routes?: RouteSet[]
  height?: string
}>()

const emit = defineEmits<{
  'select-route': [id: string | number]
}>()

// Fix default marker icons under Vite (otherwise broken paths)
L.Icon.Default.mergeOptions({ iconUrl, iconRetinaUrl, shadowUrl })

const mapEl = ref<HTMLDivElement | null>(null)

// Non-reactive Leaflet handles
let map: L.Map | null = null
let routeLayer: L.FeatureGroup | null = null
let renderToken = 0
const routePreviewCache = new Map<string, Promise<RoutePreviewData | null>>()

// Saransk, Mordovia — fallback center
const DEFAULT_CENTER: L.LatLngTuple = [54.187, 45.183]
const DEFAULT_ZOOM = 7

interface RoutePreviewData {
  geometry: L.LatLngTuple[]
  distanceKm: number
  timeMinutes: number
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => {
    switch (c) {
      case '&': return '&amp;'
      case '<': return '&lt;'
      case '>': return '&gt;'
      case '"': return '&quot;'
      case "'": return '&#39;'
      default: return c
    }
  })
}

function makeNumberedIcon(order: number, color = '#3b82f6'): L.DivIcon {
  return L.divIcon({
    className: 'route-marker',
    html: `<div class="route-marker__pin" style="background:${color}">${order}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
}

function tooltipHtml(p: RoutePoint): string {
  return (
    `<strong>${escapeHtml(p.name)}</strong>` +
    (p.address ? `<br>${escapeHtml(p.address)}` : '')
  )
}

function buildMarkers(points: RoutePoint[], color: string): L.Layer[] {
  const layers: L.Layer[] = []
  for (const p of points) {
    const marker = L.marker([p.lat, p.lon], { icon: makeNumberedIcon(p.order, p.color ?? color) })
    marker.bindTooltip(tooltipHtml(p), { direction: 'top', offset: [0, -10] })
    layers.push(marker)
  }
  return layers
}

function buildCacheKey(points: RoutePoint[]): string {
  return points.map((point) => `${point.lat.toFixed(6)},${point.lon.toFixed(6)}`).join(";")
}

async function getRoutePreview(points: RoutePoint[]): Promise<RoutePreviewData | null> {
  if (points.length < 2) return null

  const cacheKey = buildCacheKey(points)
  const cached = routePreviewCache.get(cacheKey)
  if (cached) {
    return cached
  }

  const request = fetchRoutePreview(
    points.map((point) => ({
      lat: point.lat,
      lon: point.lon,
    }))
  )
    .then((preview) => {
      if (!preview.geometry?.length) return null

      return {
        geometry: preview.geometry.map(([lat, lon]) => [lat, lon] as L.LatLngTuple),
        distanceKm: preview.distance_km,
        timeMinutes: preview.time_minutes,
      }
    })
    .catch(() => null)

  routePreviewCache.set(cacheKey, request)
  return request
}

async function renderSingle(points: RoutePoint[], token: number) {
  if (!map) return
  const valid = points.filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lon))
  if (valid.length === 0) {
    map.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
    return
  }

  const preview = await getRoutePreview(valid)
  if (!map || token !== renderToken) return

  const layers: L.Layer[] = [...buildMarkers(valid, '#3b82f6')]
  if (valid.length >= 2) {
    layers.push(
      L.polyline(
        preview?.geometry?.length ? preview.geometry : valid.map((p) => [p.lat, p.lon] as L.LatLngTuple),
        { color: '#3b82f6', weight: 4, opacity: 0.85 },
      ),
    )
  }
  routeLayer = L.featureGroup(layers).addTo(map)
  map.fitBounds(routeLayer.getBounds(), { padding: [24, 24], maxZoom: 15 })
}

async function renderMulti(routes: RouteSet[], token: number) {
  if (!map) return

  const cleaned = routes
    .map((r) => ({
      ...r,
      points: r.points.filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lon)),
    }))
    .filter((r) => r.points.length > 0)

  if (cleaned.length === 0) {
    map.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
    return
  }

  const layers: L.Layer[] = []
  // Draw non-selected first so the selected one is on top
  const ordered = [...cleaned].sort((a, b) => Number(!!a.selected) - Number(!!b.selected))
  const routePreviews = await Promise.all(
    ordered.map(async (set) => ({
      id: set.id,
      preview: await getRoutePreview(set.points),
    }))
  )
  if (!map || token !== renderToken) return
  const previewById = new Map(routePreviews.map((item) => [item.id, item.preview]))

  for (const set of ordered) {
    if (set.points.length < 2) continue
    const latlngs = previewById.get(set.id)?.geometry?.length
      ? previewById.get(set.id)!.geometry
      : set.points.map((p) => [p.lat, p.lon] as L.LatLngTuple)
    const polyline = L.polyline(latlngs, {
      color: set.color,
      weight: set.selected ? 5 : 3,
      opacity: set.selected ? 0.95 : 0.5,
      dashArray: set.selected ? undefined : '6 6',
    })
    if (!set.selected) {
      polyline.on('click', () => emit('select-route', set.id))
    }
    layers.push(polyline)
  }

  // Markers ONLY for the selected set (avoid clutter)
  const selectedSet = cleaned.find((r) => r.selected) ?? cleaned[0]
  if (selectedSet) {
    layers.push(...buildMarkers(selectedSet.points, selectedSet.color))
  }

  routeLayer = L.featureGroup(layers).addTo(map)
  map.fitBounds(routeLayer.getBounds(), { padding: [24, 24], maxZoom: 15 })
}

async function render() {
  if (!map) return
  const token = ++renderToken
  if (routeLayer) {
    map.removeLayer(routeLayer)
    routeLayer = null
  }
  if (props.routes && props.routes.length > 0) {
    await renderMulti(props.routes, token)
  } else if (props.points && props.points.length > 0) {
    await renderSingle(props.points, token)
  } else {
    map.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
  }
}

onMounted(() => {
  if (!mapEl.value) return
  map = L.map(mapEl.value, { zoomControl: true, attributionControl: false }).setView(
    DEFAULT_CENTER,
    DEFAULT_ZOOM,
  )
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '',
    maxZoom: 19,
  }).addTo(map)

  void render()
})

watch([() => props.points, () => props.routes], () => {
  void render()
}, { deep: false })

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
    routeLayer = null
  }
})
</script>

<style>
.route-map-container {
  width: 100%;
  height: 100%;
}

.route-marker {
  background: transparent;
  border: none;
}

.route-marker__pin {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #3b82f6;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}
</style>
