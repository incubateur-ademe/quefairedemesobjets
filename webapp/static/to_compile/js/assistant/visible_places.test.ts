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
  it("keeps a loaded place that stays visible", () => {
    const loaded = [place("already-there")]

    const result = merge(loaded, [place("new")], PARIS)

    expect(result.map((p) => p.uuid)).toEqual(["already-there", "new"])
  })

  it("keeps a loaded place that left the frame", () => {
    const loaded = [place("out-of-frame", 9.9, 42.0)]

    const result = merge(loaded, [place("new")], PARIS)

    expect(result.map((p) => p.uuid)).toEqual(["out-of-frame", "new"])
  })

  it("accepts at most the cap of new places per fetch", () => {
    const incoming = Array.from({ length: 30 }, (_, i) => place(`n${i}`))

    expect(merge([], incoming, PARIS)).toHaveLength(20)
  })

  it("lets the set grow past the cap across fetches", () => {
    const loaded = Array.from({ length: 20 }, (_, i) => place(`old${i}`))
    const incoming = Array.from({ length: 20 }, (_, i) => place(`new${i}`))

    expect(merge(loaded, incoming, PARIS)).toHaveLength(40)
  })

  it("does not duplicate a place present on both sides", () => {
    const result = merge([place("common")], [place("common")], PARIS)

    expect(result).toHaveLength(1)
  })

  it("does not count an already loaded place against the cap", () => {
    const loaded = [place("common")]
    const incoming = [
      place("common"),
      ...Array.from({ length: 20 }, (_, i) => place(`n${i}`)),
    ]

    expect(merge(loaded, incoming, PARIS)).toHaveLength(21)
  })

  it("evicts the farthest off-screen places past the memory cap", () => {
    const loaded = [
      place("in-frame"),
      place("near", 2.5, 48.85), // just east of PARIS
      place("far", 9.9, 42.0),
    ]

    const result = merge(loaded, [], PARIS, 20, 2)

    expect(result.map((p) => p.uuid)).toEqual(["in-frame", "near"])
  })

  it("never evicts a place in frame", () => {
    const loaded = Array.from({ length: 5 }, (_, i) => place(`in${i}`))

    const result = merge(loaded, [], PARIS, 20, 2)

    expect(result).toHaveLength(5)
  })
})
