export const buildLocationAddress = (location: {
  address?: string | null
  city?: string | null
  street?: string | null
  houseNumber?: string | null
}): string => {
  const rawAddress = location.address?.trim() ?? ''
  const city = location.city?.trim() ?? ''
  const street = location.street?.trim() ?? ''
  const houseNumber = location.houseNumber?.trim() ?? ''

  const parts: string[] = []
  if (city) {
    parts.push(`г. ${city}`)
  }
  if (street) {
    parts.push(houseNumber ? `${street}, д. ${houseNumber}` : street)
  } else if (houseNumber) {
    parts.push(`д. ${houseNumber}`)
  }

  const composedAddress = parts.join(', ')
  if (
    rawAddress &&
    (!composedAddress || rawAddress.length >= composedAddress.length)
  ) {
    return rawAddress
  }

  if (composedAddress) {
    return composedAddress
  }

  return rawAddress
}
