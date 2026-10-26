import { render } from "@testing-library/react"

import { Map, Marker } from "../../__mocks__/maplibre"
import { LocalisationMap, type MapPoint } from "./LocalisationMap"

const ORIGIN: MapPoint = {
  key: "Origin",
  latitude: 45.7,
  longitude: 4.8,
  draggable: false,
}
const correction = (latitude: number): MapPoint => ({
  key: "RevisionActeur",
  latitude,
  longitude: 4.82,
  draggable: true,
})

describe("LocalisationMap", () => {
  it("keeps the view when a marker is moved, frames again on new fixed points", () => {
    const fitBounds = jest.spyOn(Map.prototype, "fitBounds")
    const map = (points: MapPoint[]) => (
      <LocalisationMap points={points} onMove={() => {}} />
    )
    const { rerender } = render(map([ORIGIN, correction(45.72)]))
    expect(fitBounds).toHaveBeenCalledTimes(1)

    rerender(map([ORIGIN, correction(45.9)]))

    expect(fitBounds).toHaveBeenCalledTimes(1)
    const moved = Marker.instances[Marker.instances.length - 1]
    expect(moved.getLngLat()).toEqual({ lat: 45.9, lng: 4.82 })
    expect(document.querySelectorAll("[data-marker-key]")).toHaveLength(2)

    rerender(
      map([
        ORIGIN,
        correction(45.9),
        { key: "AnnuaireEntreprises", latitude: 46, longitude: 5, draggable: false },
      ]),
    )

    expect(fitBounds).toHaveBeenCalledTimes(2)
  })
})
