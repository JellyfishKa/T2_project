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

const props = defineProps<{
  points: RoutePoint[]
  height?: string
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

function makeNumberedIcon(order: number): L.DivIcon {
  return L.divIcon({
    className: 'route-marker',
    html: `<div class="route-marker__pin">${order}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
}

function renderRoute() {
  if (!map) return

  if (routeLayer) {
    map.removeLayer(routeLayer)
    routeLayer = null
  }

  const valid = props.points.filter(
    (p) => Number.isFinite(p.lat) && Number.isFinite(p.lon),
  )

  if (valid.length === 0) {
    map.setView(DEFAULT_CENTER, DEFAULT_ZOOM)
    return
  }

  const layers: L.Layer[] = []
  const latlngs: L.LatLngTuple[] = []

  for (const p of valid) {
    const ll: L.LatLngTuple = [p.lat, p.lon]
    latlngs.push(ll)
    const marker = L.marker(ll, { icon: makeNumberedIcon(p.order) })
    const tooltipHtml =
      `<strong>${escapeHtml(p.name)}</strong>` +
      (p.address ? `<br>${escapeHtml(p.address)}` : '')
    marker.bindTooltip(tooltipHtml, { direction: 'top', offset: [0, -10] })
    layers.push(marker)
  }

  if (latlngs.length >= 2) {
    layers.push(
      L.polyline(latlngs, { color: '#3b82f6', weight: 4, opacity: 0.85 }),
    )
  }

  routeLayer = L.featureGroup(layers).addTo(map)
  map.fitBounds(routeLayer.getBounds(), { padding: [24, 24], maxZoom: 15 })
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

  renderRoute()
})

watch(
  () => props.points,
  () => renderRoute(),
)

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
