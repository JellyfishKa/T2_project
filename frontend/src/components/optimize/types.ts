export type LocationPriority = 'low' | 'medium' | 'high'
export type LocationCategory = 'A' | 'B' | 'C' | 'D'

export interface Location {
  id: string
  name: string
  city: string
  street: string
  houseNumber: string
  latitude: number
  longitude: number
  timeWindowStart: string
  timeWindowEnd: string
  priority: LocationPriority
  category?: LocationCategory | null
}

export interface Constraints {
  vehicleCapacity?: number
  maxDistance?: number
  startTime?: string
  endTime?: string
  forbiddenRoads?: string[]
  maxStops?: number
}

export interface OptimizationFormData {
  routeName: string
  locations: Location[]
  notes?: string
}
