import { test as base, APIRequestContext, type APIResponse, type TestInfo } from '@playwright/test'
import type { CleanupTracker } from './test-data'
import { deleteLocation, deleteRep, deleteVehicle } from './test-data'

type Fixtures = {
  apiClient: APIRequestContext
  cleanup: CleanupTracker
}

type CleanupAttempt = {
  ok: boolean
  status?: number
  body?: string
  error?: string
}

function buildNamespace(testInfo: TestInfo): string {
  const slug = testInfo.title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 40) || 'test'

  return `e2e_${slug}_${testInfo.workerIndex}_${Date.now().toString(36)}`
}

async function runCleanupRequest(
  responsePromise: Promise<APIResponse>,
): Promise<CleanupAttempt> {
  try {
    const response = await responsePromise
    return {
      ok: [200, 204, 404].includes(response.status()),
      status: response.status(),
      body: (await response.text()).trim(),
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    return { ok: false, error: message }
  }
}

function formatCleanupError(label: string, id: string, attempt: CleanupAttempt): string {
  if (attempt.error) {
    return `${label} ${id}: ${attempt.error}`
  }

  return `${label} ${id}: ${attempt.status ?? 'unknown'}${attempt.body ? ` ${attempt.body}` : ''}`
}

async function listCrudItems(apiClient: APIRequestContext, prefix: string): Promise<Array<Record<string, unknown>>> {
  const response = await apiClient.get(`/api/v1/${prefix}?limit=1000`)
  if (!response.ok()) {
    throw new Error(`GET /api/v1/${prefix} failed: ${response.status()} ${await response.text()}`)
  }

  const payload = (await response.json()) as Record<string, unknown>
  const items = payload[prefix]
  return Array.isArray(items) ? (items as Array<Record<string, unknown>>) : []
}

async function deleteCrudItemsByField(
  apiClient: APIRequestContext,
  prefix: string,
  field: string,
  value: string,
): Promise<string[]> {
  const errors: string[] = []
  const items = await listCrudItems(apiClient, prefix)

  for (const item of items) {
    if (item[field] !== value || typeof item.id !== 'string') {
      continue
    }

    const attempt = await runCleanupRequest(apiClient.delete(`/api/v1/${prefix}/${item.id}`))
    if (!attempt.ok) {
      errors.push(formatCleanupError(prefix, item.id, attempt))
    }
  }

  return errors
}

async function cleanupRepDependencies(apiClient: APIRequestContext, repId: string): Promise<string[]> {
  const errors: string[] = []

  for (const prefix of ['visit-log', 'daily-route-overrides', 'force-majeure-events', 'skipped-visit-stash', 'visit-schedule']) {
    try {
      errors.push(...await deleteCrudItemsByField(apiClient, prefix, 'rep_id', repId))
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      errors.push(`${prefix} for rep ${repId}: ${message}`)
    }
  }

  return errors
}

async function cleanupLocationDependencies(apiClient: APIRequestContext, locationId: string): Promise<string[]> {
  const errors: string[] = []

  for (const prefix of ['visit-log', 'skipped-visit-stash', 'visit-schedule']) {
    try {
      errors.push(...await deleteCrudItemsByField(apiClient, prefix, 'location_id', locationId))
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      errors.push(`${prefix} for location ${locationId}: ${message}`)
    }
  }

  return errors
}

async function deleteRepWithFallback(apiClient: APIRequestContext, repId: string): Promise<string[]> {
  const firstAttempt = await runCleanupRequest(deleteRep(apiClient, repId, { force: true }))
  if (firstAttempt.ok) {
    return []
  }

  const dependencyErrors = firstAttempt.status === 409
    ? await cleanupRepDependencies(apiClient, repId)
    : []

  if (dependencyErrors.length > 0) {
    return dependencyErrors
  }

  const secondAttempt = await runCleanupRequest(deleteRep(apiClient, repId, { force: true }))
  return secondAttempt.ok ? [] : [formatCleanupError('rep', repId, secondAttempt)]
}

async function deleteLocationWithFallback(apiClient: APIRequestContext, locationId: string): Promise<string[]> {
  const firstAttempt = await runCleanupRequest(deleteLocation(apiClient, locationId, { force: true }))
  if (firstAttempt.ok) {
    return []
  }

  const dependencyErrors = firstAttempt.status === 409
    ? await cleanupLocationDependencies(apiClient, locationId)
    : []

  if (dependencyErrors.length > 0) {
    return dependencyErrors
  }

  const secondAttempt = await runCleanupRequest(deleteLocation(apiClient, locationId, { force: true }))
  return secondAttempt.ok ? [] : [formatCleanupError('location', locationId, secondAttempt)]
}

async function deleteCrudById(apiClient: APIRequestContext, prefix: string, id: string): Promise<string[]> {
  const attempt = await runCleanupRequest(apiClient.delete(`/api/v1/${prefix}/${id}`))
  return attempt.ok ? [] : [formatCleanupError(prefix, id, attempt)]
}

export const test = base.extend<Fixtures>({
  apiClient: async ({ playwright }, use) => {
    const client = await playwright.request.newContext({
      baseURL: process.env.API_URL ?? 'http://127.0.0.1:8000',
      extraHTTPHeaders: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    })
    await use(client)
    await client.dispose()
  },
  cleanup: async ({ apiClient }, use, testInfo) => {
    const repIds = new Set<string>()
    const vehicleIds = new Set<string>()
    const locationIds = new Set<string>()
    const visitScheduleIds = new Set<string>()
    const forceMajeureIds = new Set<string>()

    await use({
      namespace: buildNamespace(testInfo),
      trackRep: (id) => repIds.add(id),
      trackVehicle: (id) => vehicleIds.add(id),
      trackLocation: (id) => locationIds.add(id),
      trackVisitSchedule: (id) => visitScheduleIds.add(id),
      trackForceMajeure: (id) => forceMajeureIds.add(id),
    })

    const cleanupErrors: string[] = []

    for (const visitScheduleId of Array.from(visitScheduleIds).reverse()) {
      cleanupErrors.push(...await deleteCrudById(apiClient, 'visit-schedule', visitScheduleId))
    }

    for (const forceMajeureId of Array.from(forceMajeureIds).reverse()) {
      cleanupErrors.push(...await deleteCrudById(apiClient, 'force-majeure-events', forceMajeureId))
    }

    for (const repId of Array.from(repIds).reverse()) {
      cleanupErrors.push(...await deleteRepWithFallback(apiClient, repId))
    }

    for (const locationId of Array.from(locationIds).reverse()) {
      cleanupErrors.push(...await deleteLocationWithFallback(apiClient, locationId))
    }

    for (const vehicleId of Array.from(vehicleIds).reverse()) {
      const attempt = await runCleanupRequest(deleteVehicle(apiClient, vehicleId))
      if (!attempt.ok) {
        cleanupErrors.push(formatCleanupError('vehicle', vehicleId, attempt))
      }
    }

    if (cleanupErrors.length > 0) {
      throw new Error(`E2E cleanup failed:\n${cleanupErrors.join('\n')}`)
    }
  },
})

export { expect } from '@playwright/test'
