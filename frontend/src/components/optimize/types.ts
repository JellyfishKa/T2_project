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
  priority: 'low' | 'medium' | 'high'
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