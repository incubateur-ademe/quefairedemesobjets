import { Application } from "@hotwired/stimulus"
import CarteController from "../controllers/assistant/carte_controller"

const settle = () => new Promise((resolve) => setTimeout(resolve, 0))

function fakeMap({ zoom = 13 } = {}) {
  return {
    resize: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    once: jest.fn(async () => {}),
    jumpTo: jest.fn(),
    fitBounds: jest.fn(),
    remove: jest.fn(),
    getZoom: () => zoom,
    getBounds: () => ({
      getWest: () => 2.3,
      getSouth: () => 48.8,
      getEast: () => 2.4,
      getNorth: () => 48.9,
    }),
  }
}

let application: Application

async function mountWith(
  state: object,
  { geste = "reparer", longitude = 2.35, precise = false } = {},
) {
  document.body.innerHTML = `
    <div data-controller="assistant-carte"
         data-assistant-carte-url-value="/api/v1/lieux.geojson"
         data-assistant-carte-geste-value="${geste}"
         data-assistant-carte-longitude-value="${longitude}"
         data-assistant-carte-latitude-value="48.85"
         data-assistant-carte-precise-address-value="${precise}">
      <div id="assistant-carte-canvas"></div>
      <p data-assistant-carte-target="message" hidden>
        <span data-assistant-carte-target="messageText"></span>
      </p>
    </div>`
  const canvas = document.getElementById("assistant-carte-canvas")!
  Object.assign(canvas, { assistantMap: state })
  // jsdom lays nothing out: a parked canvas has no width, a shown one does.
  Object.defineProperty(canvas, "clientWidth", { value: 800 })
  application = Application.start()
  application.register("assistant-carte", CarteController)
  await settle()
  return canvas
}

function fakeMarker() {
  const marker = {
    remove: jest.fn(),
    getElement: () => document.createElement("a"),
    setLngLat: () => marker,
    addTo: () => marker,
  }
  return marker
}

const PLACE = { uuid: "a", nom: "A", longitude: 2.35, latitude: 48.85, bonus: false }

function persisted(map = fakeMap(), { withPlace = true } = {}) {
  const marker = fakeMarker()
  return {
    map,
    Marker: jest.fn(fakeMarker),
    markers: new Map(withPlace ? [["a", marker]] : []),
    places: withPlace ? [PLACE] : [],
    addressMarker: null,
    key: "reparer|",
    address: [2.35, 48.85],
    lastRequestedUrl: "",
    needsFit: false,
    onMoveEnd: null,
    marker,
  }
}

function respond(response: { ok: boolean; features?: object[] }) {
  global.fetch = jest.fn(async () => ({
    ok: response.ok,
    status: response.ok ? 200 : 500,
    headers: { get: () => null },
    json: async () => ({
      type: "FeatureCollection",
      features: response.features ?? [],
    }),
  })) as unknown as typeof fetch
}

const message = () =>
  document.querySelector<HTMLElement>("[data-assistant-carte-target=message]")!

function moveEnd(state: ReturnType<typeof persisted>) {
  const [, handler] = state.map.on.mock.calls.find(([event]) => event === "moveend")!
  handler()
}

beforeEach(() => respond({ ok: true }))
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

  it("starts a new search on a new address", async () => {
    const state = persisted()

    await mountWith(state, { longitude: 5.37 })

    expect(state.map.jumpTo).toHaveBeenCalled()
    expect(state.marker.remove).toHaveBeenCalled()
    expect(state.places).toEqual([])
  })

  it("keeps its pins when the map moves", async () => {
    const state = persisted()
    await mountWith(state)

    moveEnd(state)
    await settle()

    expect(state.marker.remove).not.toHaveBeenCalled()
    expect(state.markers.has("a")).toBe(true)
  })

  it.each([
    [false, 0],
    [true, 1],
  ])("shows the red pin for a precise address only (%s)", async (precise, count) => {
    const state = persisted()

    await mountWith(state, { precise })

    expect(state.Marker).toHaveBeenCalledTimes(count)
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

describe("assistant map messages", () => {
  it("says when the visible area has no place", async () => {
    await mountWith(persisted(fakeMap(), { withPlace: false }))
    await settle()

    expect(message().hidden).toBe(false)
    expect(message().textContent).toContain("Aucun lieu trouvé ici")
  })

  it("says when the places failed to load, and retries on the next move", async () => {
    respond({ ok: false })
    const state = persisted(fakeMap(), { withPlace: false })
    await mountWith(state)
    await settle()

    expect(message().textContent).toContain("n'ont pas pu être chargés")

    moveEnd(state)
    await settle()
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  it("asks to zoom in, without any request, when zoomed out too far", async () => {
    await mountWith(persisted(fakeMap({ zoom: 8 })))

    expect(message().textContent).toContain("Zoomez sur la carte")
    expect(
      document.querySelector<HTMLElement>("[data-controller]")!.dataset.zoomedOut,
    ).toBe("true")
    expect(global.fetch).not.toHaveBeenCalled()
  })
})
