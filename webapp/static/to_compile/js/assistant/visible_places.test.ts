import {
  isInArea,
  merge,
  placesFromGeoJSON,
  type Area,
  type Place,
} from "./visible_places"

const PARIS: Area = { west: 2.2, south: 48.8, east: 2.4, north: 48.9 }

function place(uuid: string, longitude = 2.3, latitude = 48.85): Place {
  return { uuid, nom: `Lieu ${uuid}`, bonus: false, longitude, latitude }
}

describe("placesFromGeoJSON", () => {
  it("flattens a FeatureCollection into places", () => {
    const collection = {
      features: [
        {
          geometry: { coordinates: [2.35, 48.86] as [number, number] },
          properties: { uuid: "a", nom: "Atelier", bonus: true },
        },
      ],
    }

    expect(placesFromGeoJSON(collection)).toEqual([
      { uuid: "a", nom: "Atelier", bonus: true, longitude: 2.35, latitude: 48.86 },
    ])
  })
})

describe("isInArea", () => {
  it("accepts a place inside", () => {
    expect(isInArea(place("a", 2.3, 48.85), PARIS)).toBe(true)
  })

  it("rejects a place west of the area", () => {
    expect(isInArea(place("a", 2.0, 48.85), PARIS)).toBe(false)
  })

  it("accepts a place exactly on the edge", () => {
    expect(isInArea(place("a", 2.2, 48.8), PARIS)).toBe(true)
  })
})

describe("merge", () => {
  it("keeps a shown place that stays visible", () => {
    const shown = [place("already-there")]

    const result = merge(shown, [place("new")], PARIS)

    expect(result.map((p) => p.uuid)).toEqual(["already-there", "new"])
  })

  it("drops a place that left the frame", () => {
    const shown = [place("gone", 9.9, 42.0)]

    const result = merge(shown, [place("new")], PARIS)

    expect(result.map((p) => p.uuid)).toEqual(["new"])
  })

  it("never exceeds the cap", () => {
    const incoming = Array.from({ length: 30 }, (_, i) => place(`n${i}`))

    expect(merge([], incoming, PARIS)).toHaveLength(20)
  })

  it("gives priority to kept places when the cap is reached", () => {
    const shown = Array.from({ length: 20 }, (_, i) => place(`old${i}`))
    const incoming = Array.from({ length: 20 }, (_, i) => place(`new${i}`))

    const result = merge(shown, incoming, PARIS)

    expect(result).toHaveLength(20)
    expect(result.every((p) => p.uuid.startsWith("old"))).toBe(true)
  })

  it("does not duplicate a place present on both sides", () => {
    const result = merge([place("common")], [place("common")], PARIS)

    expect(result).toHaveLength(1)
  })
})
