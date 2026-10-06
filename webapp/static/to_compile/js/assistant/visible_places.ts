export const MAX_PLACES = 20

export type Place = {
  uuid: string
  nom: string
  bonus: boolean
  longitude: number
  latitude: number
}

export type Area = {
  west: number
  south: number
  east: number
  north: number
}

type Feature = {
  geometry: { coordinates: [number, number] }
  properties: { uuid: string; nom: string; bonus: boolean }
}

export function placesFromGeoJSON(collection: { features: Feature[] }): Place[] {
  return collection.features.map(({ geometry, properties }) => ({
    uuid: properties.uuid,
    nom: properties.nom,
    bonus: properties.bonus,
    longitude: geometry.coordinates[0],
    latitude: geometry.coordinates[1],
  }))
}

export function isInArea(place: Place, area: Area): boolean {
  return (
    place.longitude >= area.west &&
    place.longitude <= area.east &&
    place.latitude >= area.south &&
    place.latitude <= area.north
  )
}

/**
 * Merges the places already shown with the ones that just arrived.
 *
 * Places still visible come first: a place under the user's eyes must neither
 * move nor vanish as long as it stays in frame (#3356). Incoming ones fill up
 * to the cap.
 */
export function merge(
  shown: Place[],
  incoming: Place[],
  area: Area,
  cap: number = MAX_PLACES,
): Place[] {
  const kept = shown.filter((place) => isInArea(place, area))
  const merged = new Map(kept.map((place) => [place.uuid, place]))

  for (const place of incoming) {
    if (merged.size >= cap) break
    merged.set(place.uuid, place)
  }

  return [...merged.values()]
}
