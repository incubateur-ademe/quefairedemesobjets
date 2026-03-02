import "@testing-library/jest-dom"
import { Application } from "@hotwired/stimulus"
import MapSearchController from "../controllers/admin/map_search_controller"

// Minimal OpenLayers global mock — only the surface used by map_search_controller.ts
const mockSetView = jest.fn()
const mockFeatureCollectionPush = jest.fn()
const mockClearFeatures = jest.fn()

const mockWidget = {
  options: { id: "id_localisation" },
  clearFeatures: mockClearFeatures,
  featureCollection: { push: mockFeatureCollectionPush },
  map: { setView: mockSetView },
}

;(globalThis as any).ol = {
  Feature: jest.fn().mockImplementation((opts) => opts),
  geom: {
    Point: jest.fn().mockImplementation((coords) => ({ coords })),
  },
  proj: {
    fromLonLat: jest.fn().mockImplementation((coords) => coords),
  },
  View: jest.fn().mockImplementation((opts) => opts),
}

function buildDOM(addressFieldIds = "") {
  document.body.innerHTML = `
    <input id="id_adresse" type="text" value="10 rue de Rivoli" />
    <input id="id_code_postal" type="text" value="75001" />
    <input id="id_ville" type="text" value="Paris" />
    <textarea id="id_localisation"></textarea>

    <div
      data-controller="map-search"
      data-map-search-widget-id-value="id_localisation"
      data-map-search-address-field-ids-value="${addressFieldIds}"
    >
      <input data-map-search-target="input" type="text" />
      <input
        type="button"
        data-action="click->map-search#search"
        value="Placer sur la carte"
      />
    </div>
  `
}

function startApplication() {
  const application = Application.start()
  application.register("map-search", MapSearchController)
  return application
}

const tick = () => new Promise<void>((r) => setTimeout(r, 0))

describe("MapSearchController", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(globalThis as any).geodjangoWidgets = { id_localisation: mockWidget }
  })

  afterEach(() => {
    delete (globalThis as any).geodjangoWidgets
  })

  describe("connect() — address pre-fill", () => {
    it("joins non-empty address field values into the input", async () => {
      buildDOM("id_adresse,id_code_postal,id_ville")
      startApplication()
      await tick()

      const input = document.querySelector<HTMLInputElement>(
        '[data-map-search-target="input"]',
      )!
      expect(input.value).toBe("10 rue de Rivoli, 75001, Paris")
    })

    it("skips empty address fields", async () => {
      buildDOM("id_adresse,id_code_postal,id_ville")
      ;(document.getElementById("id_code_postal") as HTMLInputElement).value = ""
      startApplication()
      await tick()

      const input = document.querySelector<HTMLInputElement>(
        '[data-map-search-target="input"]',
      )!
      expect(input.value).toBe("10 rue de Rivoli, Paris")
    })

    it("leaves the input empty when addressFieldIds is not set", async () => {
      buildDOM("")
      startApplication()
      await tick()

      const input = document.querySelector<HTMLInputElement>(
        '[data-map-search-target="input"]',
      )!
      expect(input.value).toBe("")
    })
  })

  describe("search() — successful geocoding result", () => {
    beforeEach(() => {
      buildDOM("id_adresse")
      startApplication()
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({
          features: [
            {
              geometry: { coordinates: [2.3469, 48.8592], type: "Point" },
            },
          ],
        }),
      })
    })

    async function triggerSearch(address = "Mairie de Paris") {
      await tick()
      const input = document.querySelector<HTMLInputElement>(
        '[data-map-search-target="input"]',
      )!
      input.value = address
      document
        .querySelector<HTMLInputElement>('[data-action="click->map-search#search"]')!
        .click()
      await tick()
    }

    it("calls clearFeatures on the widget", async () => {
      await triggerSearch()
      expect(mockClearFeatures).toHaveBeenCalledTimes(1)
    })

    it("pushes a projected feature to the widget featureCollection", async () => {
      await triggerSearch()
      expect(mockFeatureCollectionPush).toHaveBeenCalledTimes(1)
      expect((globalThis as any).ol.proj.fromLonLat).toHaveBeenCalledWith([
        2.3469, 48.8592,
      ])
    })

    it("sets the map view to zoom 15 centred on the returned coordinates", async () => {
      await triggerSearch()
      expect(mockSetView).toHaveBeenCalledTimes(1)
      const viewArg = (globalThis as any).ol.View.mock.calls[0][0]
      expect(viewArg.zoom).toBe(15)
    })

    it("does nothing when the input is empty", async () => {
      await triggerSearch("")
      expect(mockClearFeatures).not.toHaveBeenCalled()
      expect(global.fetch).not.toHaveBeenCalled()
    })
  })

  describe("search() — no geocoding result", () => {
    it("does not touch the widget when the API returns an empty features array", async () => {
      buildDOM("id_adresse")
      startApplication()
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ features: [] }),
      })

      await tick()
      const input = document.querySelector<HTMLInputElement>(
        '[data-map-search-target="input"]',
      )!
      input.value = "lieu inconnu"
      document
        .querySelector<HTMLInputElement>('[data-action="click->map-search#search"]')!
        .click()
      await tick()

      expect(mockClearFeatures).not.toHaveBeenCalled()
      expect(mockFeatureCollectionPush).not.toHaveBeenCalled()
      expect(mockSetView).not.toHaveBeenCalled()
    })
  })

  describe("search() — network failure", () => {
    it("does not touch the widget when fetch rejects", async () => {
      buildDOM("id_adresse")
      startApplication()
      global.fetch = jest.fn().mockRejectedValue(new Error("Network error"))
      jest.spyOn(console, "error").mockImplementation(() => {})

      await tick()
      const input = document.querySelector<HTMLInputElement>(
        '[data-map-search-target="input"]',
      )!
      input.value = "anywhere"
      document
        .querySelector<HTMLInputElement>('[data-action="click->map-search#search"]')!
        .click()
      await tick()

      expect(mockClearFeatures).not.toHaveBeenCalled()
      expect(mockFeatureCollectionPush).not.toHaveBeenCalled()
    })
  })
})
