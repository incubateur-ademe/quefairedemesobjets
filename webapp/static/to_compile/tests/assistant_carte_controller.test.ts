import { Application } from "@hotwired/stimulus"
import CarteController from "../controllers/assistant/carte_controller"

const settle = () => new Promise((resolve) => setTimeout(resolve, 0))

function fakeMap() {
  return {
    resize: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    once: jest.fn(async () => {}),
    jumpTo: jest.fn(),
    fitBounds: jest.fn(),
    remove: jest.fn(),
    getZoom: () => 13,
    getBounds: () => ({
      getWest: () => 2.3,
      getSouth: () => 48.8,
      getEast: () => 2.4,
      getNorth: () => 48.9,
    }),
  }
}

let application: Application

async function mountWith(state: object, { geste = "reparer", longitude = 2.35 } = {}) {
  document.body.innerHTML = `
    <div data-controller="assistant-carte"
         data-assistant-carte-url-value="/api/v1/lieux.geojson"
         data-assistant-carte-geste-value="${geste}"
         data-assistant-carte-longitude-value="${longitude}"
         data-assistant-carte-latitude-value="48.85">
      <div id="assistant-carte-canvas"></div>
    </div>`
  const canvas = document.getElementById("assistant-carte-canvas")!
  Object.assign(canvas, { assistantMap: state })
  application = Application.start()
  application.register("assistant-carte", CarteController)
  await settle()
  return canvas
}

function persisted(map = fakeMap()) {
  const marker = { remove: jest.fn(), getElement: () => document.createElement("a") }
  return {
    map,
    Marker: jest.fn(),
    markers: new Map([["a", marker]]),
    places: [{ uuid: "a", nom: "A", longitude: 2.35, latitude: 48.85, bonus: false }],
    addressMarker: null,
    key: "reparer|",
    address: [2.35, 48.85],
    lastRequestedUrl: "",
    needsFit: false,
    onMoveEnd: null,
    marker,
  }
}

afterEach(() => application?.stop())

describe("assistant map persisted across screens", () => {
  it("reuses the map and its pins for the same search", async () => {
    const state = persisted()

    await mountWith(state)

    expect(state.map.resize).toHaveBeenCalled()
    expect(state.map.jumpTo).not.toHaveBeenCalled()
    expect(state.markers.size).toBe(1)
  })

  it("drops the pins of another geste", async () => {
    const state = persisted()

    await mountWith(state, { geste: "trier" })

    expect(state.marker.remove).toHaveBeenCalled()
    expect(state.places).toEqual([])
    expect(state.key).toBe("trier|")
  })

  it("recenters on a new address", async () => {
    const state = persisted()

    await mountWith(state, { longitude: 5.37 })

    expect(state.map.jumpTo).toHaveBeenCalled()
    expect(state.needsFit).toBe(true)
  })

  it("releases the map once its canvas is gone, not while Turbo moves it", async () => {
    const kept = persisted()
    const canvas = await mountWith(kept)
    document.body.append(canvas)
    document.querySelector("[data-controller]")!.remove()
    await settle()
    expect(kept.map.remove).not.toHaveBeenCalled()

    const dropped = persisted()
    await mountWith(dropped)
    document.body.innerHTML = ""
    await settle()
    await settle()
    expect(dropped.map.remove).toHaveBeenCalled()
  })
})
