import type { LocationCategory, LocationPriority } from './types'

const CATEGORY_TO_PRIORITY: Record<LocationCategory, LocationPriority> = {
  A: 'high',
  B: 'medium',
  C: 'low',
  D: 'low',
}

export const normalizeLocationCategory = (
  category?: string | null
): LocationCategory | null => {
  if (!category) return null

  const normalizedCategory = category.trim().toUpperCase()
  if (normalizedCategory in CATEGORY_TO_PRIORITY) {
    return normalizedCategory as LocationCategory
  }

  return null
}

export const normalizeLocationPriority = (
  priority?: string | null
): LocationPriority | null => {
  if (!priority) return null

  const normalizedPriority = priority.trim().toLowerCase()
  if (
    normalizedPriority === 'low' ||
    normalizedPriority === 'medium' ||
    normalizedPriority === 'high'
  ) {
    return normalizedPriority
  }

  return null
}

export const resolveLocationPriority = ({
  priority,
  category,
}: {
  priority?: string | null
  category?: string | null
}): LocationPriority => {
  const normalizedPriority = normalizeLocationPriority(priority)
  if (normalizedPriority) {
    return normalizedPriority
  }

  const normalizedCategory = normalizeLocationCategory(category)
  if (normalizedCategory) {
    return CATEGORY_TO_PRIORITY[normalizedCategory]
  }

  return 'medium'
}
