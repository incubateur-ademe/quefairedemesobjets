import {
  estDansLaZone,
  fusionner,
  lieuxDepuisGeoJSON,
  type Lieu,
  type Zone,
} from "./lieux_visibles"

const PARIS: Zone = { ouest: 2.2, sud: 48.8, est: 2.4, nord: 48.9 }

function lieu(uuid: string, longitude = 2.3, latitude = 48.85): Lieu {
  return { uuid, nom: `Lieu ${uuid}`, bonus: false, longitude, latitude }
}

describe("lieuxDepuisGeoJSON", () => {
  it("aplatit une FeatureCollection en lieux", () => {
    const collection = {
      features: [
        {
          geometry: { coordinates: [2.35, 48.86] as [number, number] },
          properties: { uuid: "a", nom: "Atelier", bonus: true },
        },
      ],
    }

    expect(lieuxDepuisGeoJSON(collection)).toEqual([
      { uuid: "a", nom: "Atelier", bonus: true, longitude: 2.35, latitude: 48.86 },
    ])
  })
})

describe("estDansLaZone", () => {
  it("accepte un lieu à l'intérieur", () => {
    expect(estDansLaZone(lieu("a", 2.3, 48.85), PARIS)).toBe(true)
  })

  it("refuse un lieu à l'ouest de la zone", () => {
    expect(estDansLaZone(lieu("a", 2.0, 48.85), PARIS)).toBe(false)
  })

  it("accepte un lieu exactement sur la bordure", () => {
    expect(estDansLaZone(lieu("a", 2.2, 48.8), PARIS)).toBe(true)
  })
})

describe("fusionner", () => {
  it("conserve un lieu déjà affiché qui reste visible", () => {
    const affiches = [lieu("deja-la")]

    const resultat = fusionner(affiches, [lieu("nouveau")], PARIS)

    expect(resultat.map((l) => l.uuid)).toEqual(["deja-la", "nouveau"])
  })

  it("retire un lieu sorti du cadre", () => {
    const affiches = [lieu("parti", 9.9, 42.0)]

    const resultat = fusionner(affiches, [lieu("nouveau")], PARIS)

    expect(resultat.map((l) => l.uuid)).toEqual(["nouveau"])
  })

  it("ne dépasse jamais le plafond", () => {
    const nouveaux = Array.from({ length: 30 }, (_, i) => lieu(`n${i}`))

    expect(fusionner([], nouveaux, PARIS)).toHaveLength(20)
  })

  it("donne la priorité aux lieux conservés quand le plafond est atteint", () => {
    const affiches = Array.from({ length: 20 }, (_, i) => lieu(`ancien${i}`))
    const nouveaux = Array.from({ length: 20 }, (_, i) => lieu(`nouveau${i}`))

    const resultat = fusionner(affiches, nouveaux, PARIS)

    expect(resultat).toHaveLength(20)
    expect(resultat.every((l) => l.uuid.startsWith("ancien"))).toBe(true)
  })

  it("ne duplique pas un lieu présent des deux côtés", () => {
    const resultat = fusionner([lieu("commun")], [lieu("commun")], PARIS)

    expect(resultat).toHaveLength(1)
  })
})
