import { APIRequestContext, type APIResponse } from '@playwright/test'

export interface RepData {
  id: string
  name: string
  status: string
}

export interface VehicleData {
  id: string
  name: string
}

export interface LocationData {
  id: string
  name: string
  category?: 'A' | 'B' | 'C' | 'D' | null
}

export interface CleanupTracker {
  namespace: string
  trackRep(id: string): void
  trackVehicle(id: string): void
  trackLocation(id: string): void
  trackVisitSchedule(id: string): void
  trackForceMajeure(id: string): void
}

export async function createRep(
  api: APIRequestContext,
  name: string,
  status = 'active',
  cleanup?: CleanupTracker,
): Promise<RepData> {
  const res = await api.post('/api/v1/reps/', {
    data: { name, status },
  })
  if (!res.ok()) {
    throw new Error(`createRep failed: ${res.status()} ${await res.text()}`)
  }
  const rep = (await res.json()) as RepData
  cleanup?.trackRep(rep.id)
  return rep
}

export async function deleteRep(
  api: APIRequestContext,
  id: string,
  options?: { force?: boolean },
): Promise<APIResponse> {
  const query = options?.force ? '?force=true' : ''
  return api.delete(`/api/v1/reps/${id}${query}`)
}

export async function createVehicle(
  api: APIRequestContext,
  name: string,
  fuelPrice = 50,
  consumptionCity = 10,
  consumptionHighway = 7,
  cleanup?: CleanupTracker,
): Promise<VehicleData> {
  const res = await api.post('/api/v1/routing/', {
    data: {
      name,
      fuel_price_rub: fuelPrice,
      consumption_city_l_100km: consumptionCity,
      consumption_highway_l_100km: consumptionHighway,
    },
  })
  if (!res.ok()) {
    throw new Error(`createVehicle failed: ${res.status()} ${await res.text()}`)
  }
  const vehicle = (await res.json()) as VehicleData
  cleanup?.trackVehicle(vehicle.id)
  return vehicle
}

export async function deleteVehicle(api: APIRequestContext, id: string): Promise<APIResponse> {
  return api.delete(`/api/v1/routing/${id}`)
}

export async function createLocation(
  api: APIRequestContext,
  name: string,
  category: 'A' | 'B' | 'C' | 'D' = 'C',
  cleanup?: CleanupTracker,
): Promise<LocationData> {
  const res = await api.post('/api/v1/locations/', {
    data: {
      name,
      lat: 54.1871,
      lon: 45.1749,
      time_window_start: '09:00',
      time_window_end: '18:00',
      category,
      city: 'Саранск',
      district: 'г.о. Саранск',
      address: 'ул. Советская, 35',
    },
  })
  if (!res.ok()) {
    throw new Error(`createLocation failed: ${res.status()} ${await res.text()}`)
  }
  const location = (await res.json()) as LocationData
  cleanup?.trackLocation(location.id)
  return location
}

export async function deleteLocation(
  api: APIRequestContext,
  id: string,
  options?: { force?: boolean },
): Promise<APIResponse> {
  const query = options?.force ? '?force=true' : ''
  return api.delete(`/api/v1/locations/${id}${query}`)
}

export async function ensureScheduleSeedLocations(
  api: APIRequestContext,
  count = 3,
  cleanup?: CleanupTracker,
): Promise<LocationData[]> {
  const seedPrefix = cleanup?.namespace ?? 'E2E_Schedule'
  const seedNames = Array.from({ length: count }, (_, index) => `${seedPrefix}_Location_${index + 1}`)
  const existingRes = await api.get('/api/v1/locations/')
  if (!existingRes.ok()) {
    throw new Error(`fetchLocations failed: ${existingRes.status()} ${await existingRes.text()}`)
  }

  const existing = (await existingRes.json()) as LocationData[]
  const byName = new Map(existing.map((location) => [location.name, location]))
  const ensured: LocationData[] = []

  for (const seedName of seedNames) {
    const current = byName.get(seedName)
    if (current?.category === 'C') {
      cleanup?.trackLocation(current.id)
      ensured.push(current)
      continue
    }

    ensured.push(await createLocation(api, seedName, 'C', cleanup))
  }

  return ensured
}

export async function ensureGeneratedSchedule(
  api: APIRequestContext,
  month: string,
  repIds: string[],
  cleanup?: CleanupTracker,
): Promise<void> {
  await ensureScheduleSeedLocations(api, 3, cleanup)

  const res = await api.post('/api/v1/schedule/generate?force=true', {
    data: { month, rep_ids: repIds },
  })
  if (!res.ok()) {
    throw new Error(`generateSchedule failed: ${res.status()} ${await res.text()}`)
  }

  await trackGeneratedScheduleEntries(api, month, repIds, cleanup)
}

export async function trackGeneratedScheduleEntries(
  api: APIRequestContext,
  month: string,
  repIds: string[],
  cleanup?: CleanupTracker,
): Promise<void> {
  if (!cleanup) {
    return
  }

  const scheduleRes = await api.get('/api/v1/visit-schedule?limit=20000')
  if (!scheduleRes.ok()) {
    throw new Error(`fetchGeneratedVisitSchedule failed: ${scheduleRes.status()} ${await scheduleRes.text()}`)
  }

  const payload = (await scheduleRes.json()) as {
    'visit-schedule'?: Array<{
      id?: string
      rep_id?: string
    }>
  }

  for (const visit of payload['visit-schedule'] ?? []) {
    if (
      typeof visit.id === 'string'
      && typeof visit.rep_id === 'string'
      && repIds.includes(visit.rep_id)
    ) {
      cleanup.trackVisitSchedule(visit.id)
    }
  }
}

export function currentMonth(offset = 0): string {
  const now = new Date()
  const shifted = new Date(now.getFullYear(), now.getMonth() + offset, 1)
  const y = shifted.getFullYear()
  const m = String(shifted.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}`
}

export function rootApiUrl(path: string): string {
  const baseUrl = process.env.API_URL ?? 'http://127.0.0.1:8000'
  return new URL(path, `${new URL(baseUrl).origin}/`).toString()
}
