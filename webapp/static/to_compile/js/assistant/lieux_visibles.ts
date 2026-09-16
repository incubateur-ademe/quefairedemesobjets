export const NOMBRE_MAX_LIEUX = 20

export type Lieu = {
  uuid: string
  nom: string
  bonus: boolean
  longitude: number
  latitude: number
}

export type Zone = {
  ouest: number
  sud: number
  est: number
  nord: number
}

type Feature = {
  geometry: { coordinates: [number, number] }
  properties: { uuid: string; nom: string; bonus: boolean }
}

export function lieuxDepuisGeoJSON(collection: { features: Feature[] }): Lieu[] {
  return collection.features.map(({ geometry, properties }) => ({
    uuid: properties.uuid,
    nom: properties.nom,
    bonus: properties.bonus,
    longitude: geometry.coordinates[0],
    latitude: geometry.coordinates[1],
  }))
}

export function estDansLaZone(lieu: Lieu, zone: Zone): boolean {
  return (
    lieu.longitude >= zone.ouest &&
    lieu.longitude <= zone.est &&
    lieu.latitude >= zone.sud &&
    lieu.latitude <= zone.nord
  )
}

/**
 * Fusionne les lieux déjà affichés avec ceux qui viennent d'arriver.
 *
 * Les lieux encore visibles passent en premier : un lieu sous les yeux de
 * l'usager ne doit ni bouger ni disparaître tant qu'il reste dans le cadre
 * (#3356). Les nouveaux complètent jusqu'au plafond.
 */
export function fusionner(
  affiches: Lieu[],
  nouveaux: Lieu[],
  zone: Zone,
  plafond: number = NOMBRE_MAX_LIEUX,
): Lieu[] {
  const conserves = affiches.filter((lieu) => estDansLaZone(lieu, zone))
  const fusion = new Map(conserves.map((lieu) => [lieu.uuid, lieu]))

  for (const lieu of nouveaux) {
    if (fusion.size >= plafond) break
    fusion.set(lieu.uuid, lieu)
  }

  return [...fusion.values()]
}
