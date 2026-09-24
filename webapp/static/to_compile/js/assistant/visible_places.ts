/** New places accepted per fetch: the server never sends more than this. */
export const MAX_PLACES = 20
/** Places kept in memory across moves; beyond it, the farthest off-screen go. */
export const MEMORY_CAP = 200

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
 * Merges the places already loaded with the ones that just arrived.
 *
 * Everything already loaded stays: a place the user has seen must neither
 * move nor vanish as they browse, whether it is still in frame or just out of
 * it (#3356, extended to browsing). Incoming places are added up to `cap`
 * per fetch, so the set grows as the user explores.
 *
 * Memory is bounded by `memoryCap`: past it, the off-screen places farthest
 * from the current area are dropped first. Places in frame are never evicted.
 */
export function merge(
  loaded: Place[],
  incoming: Place[],
  area: Area,
  cap: number = MAX_PLACES,
  memoryCap: number = MEMORY_CAP,
): Place[] {
  const merged = new Map(loaded.map((place) => [place.uuid, place]))

  let added = 0
  for (const place of incoming) {
    if (added >= cap) break
    if (merged.has(place.uuid)) continue
    merged.set(place.uuid, place)
    added += 1
  }

  return evict([...merged.values()], area, memoryCap)
}

function evict(places: Place[], area: Area, memoryCap: number): Place[] {
  if (places.length <= memoryCap) return places

  const inFrame = places.filter((place) => isInArea(place, area))
  const offScreen = places
    .filter((place) => !isInArea(place, area))
    .sort((a, b) => distanceTo(a, area) - distanceTo(b, area))

  return [...inFrame, ...offScreen.slice(0, Math.max(memoryCap - inFrame.length, 0))]
}

/** Squared distance in degrees to the area center: only used to rank, never shown. */
function distanceTo(place: Place, area: Area): number {
  const dx = place.longitude - (area.west + area.east) / 2
  const dy = place.latitude - (area.south + area.north) / 2
  return dx * dx + dy * dy
}
