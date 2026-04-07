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

export interface RoutePoint {
  id: string
  name: string
  address?: string | null
  lat: number
  lon: number
  order: number
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

// Saransk, Mordovia — fallback center
const DEFAULT_CENTER: L.LatLngTuple = [54.187, 45.183]
const DEFAULT_ZOOM = 7

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
    const marker = L.marker([p.lat, p.lon], { icon: makeNumberedIcon(p.order, color) })
    marker.bindTooltip(tooltipHtml(p), { direction: 'top', offset: [0, -10] })
    layers.push(marker)
  }
  return layers
}

function renderSingle(points: RoutePoint[]) {
  if (!map) return
  const valid = points.filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lon))
  if (valid.length === 0) {
    map.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
    return
  }
  const layers: L.Layer[] = [...buildMarkers(valid, '#3b82f6')]
  if (valid.length >= 2) {
    layers.push(
      L.polyline(
        valid.map((p) => [p.lat, p.lon] as L.LatLngTuple),
        { color: '#3b82f6', weight: 4, opacity: 0.85 },
      ),
    )
  }
  routeLayer = L.featureGroup(layers).addTo(map)
  map.fitBounds(routeLayer.getBounds(), { padding: [24, 24], maxZoom: 15 })
}

function renderMulti(routes: RouteSet[]) {
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

  for (const set of ordered) {
    if (set.points.length < 2) continue
    const latlngs = set.points.map((p) => [p.lat, p.lon] as L.LatLngTuple)
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

function render() {
  if (!map) return
  if (routeLayer) {
    map.removeLayer(routeLayer)
    routeLayer = null
  }
  if (props.routes && props.routes.length > 0) {
    renderMulti(props.routes)
  } else if (props.points && props.points.length > 0) {
    renderSingle(props.points)
  } else {
    map.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
  }
}

onMounted(() => {
  if (!mapEl.value) return
  map = L.map(mapEl.value, { zoomControl: true }).setView(
    DEFAULT_CENTER,
    DEFAULT_ZOOM,
  )
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map)

  render()
})

watch([() => props.points, () => props.routes], () => render(), { deep: false })

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
