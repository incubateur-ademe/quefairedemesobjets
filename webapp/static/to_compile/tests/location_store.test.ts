import {
  readStoredLocation,
  hasCompleteLocation,
  persistLocation,
  injectLocationIntoSrc,
} from "../js/location_store"

describe("location_store", () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  describe("readStoredLocation", () => {
    it("reads the three keys from sessionStorage", () => {
      sessionStorage.setItem("adresse", "Auray")
      sessionStorage.setItem("latitude", "47.66")
      sessionStorage.setItem("longitude", "-2.99")
      expect(readStoredLocation()).toEqual({
        adresse: "Auray",
        latitude: "47.66",
        longitude: "-2.99",
      })
    })

    it("returns nulls when nothing is stored", () => {
      expect(readStoredLocation()).toEqual({
        adresse: null,
        latitude: null,
        longitude: null,
      })
    })
  })

  describe("hasCompleteLocation", () => {
    it("requires both latitude and longitude", () => {
      expect(hasCompleteLocation({ adresse: "x", latitude: "1", longitude: "2" })).toBe(
        true,
      )
      expect(
        hasCompleteLocation({ adresse: "x", latitude: "1", longitude: null }),
      ).toBe(false)
      expect(
        hasCompleteLocation({ adresse: "x", latitude: null, longitude: "2" }),
      ).toBe(false)
      expect(
        hasCompleteLocation({ adresse: null, latitude: null, longitude: null }),
      ).toBe(false)
    })
  })

  describe("persistLocation", () => {
    it("writes present values", () => {
      persistLocation({ adresse: "Auray", latitude: "47.66", longitude: "-2.99" })
      expect(sessionStorage.getItem("adresse")).toBe("Auray")
      expect(sessionStorage.getItem("latitude")).toBe("47.66")
      expect(sessionStorage.getItem("longitude")).toBe("-2.99")
    })

    it("skips empty values and does not rewrite unchanged ones", () => {
      sessionStorage.setItem("latitude", "47.66")
      const setItem = jest.spyOn(Storage.prototype, "setItem")

      persistLocation({ adresse: "", latitude: "47.66", longitude: "-2.99" })

      expect(setItem).not.toHaveBeenCalledWith("adresse", "")
      expect(setItem).not.toHaveBeenCalledWith("latitude", "47.66") // unchanged
      expect(setItem).toHaveBeenCalledWith("longitude", "-2.99")
      setItem.mockRestore()
    })
  })

  describe("injectLocationIntoSrc", () => {
    it("appends namespaced params and preserves existing query", () => {
      sessionStorage.setItem("latitude", "47.66")
      sessionStorage.setItem("longitude", "-2.99")
      sessionStorage.setItem("adresse", "Auray")

      const result = injectLocationIntoSrc(
        "/carte/tous-les-gestes/?sc_id=88",
        "tous-les-gestes_map",
        readStoredLocation(),
      )

      const url = new URL(result, "https://example.test")
      expect(url.pathname).toBe("/carte/tous-les-gestes/")
      expect(url.searchParams.get("sc_id")).toBe("88")
      expect(url.searchParams.get("tous-les-gestes_map-latitude")).toBe("47.66")
      expect(url.searchParams.get("tous-les-gestes_map-longitude")).toBe("-2.99")
      expect(url.searchParams.get("tous-les-gestes_map-adresse")).toBe("Auray")
    })

    it("returns src unchanged when coordinates are incomplete", () => {
      const src = "/carte/x/?sc_id=1"
      expect(
        injectLocationIntoSrc(src, "x_map", {
          adresse: "Auray",
          latitude: "47.66",
          longitude: null,
        }),
      ).toBe(src)
    })

    it("omits adresse when absent but coords present", () => {
      const result = injectLocationIntoSrc("/carte/x/?sc_id=1", "x_map", {
        adresse: null,
        latitude: "47.66",
        longitude: "-2.99",
      })
      const url = new URL(result, "https://example.test")
      expect(url.searchParams.get("x_map-latitude")).toBe("47.66")
      expect(url.searchParams.has("x_map-adresse")).toBe(false)
    })

    it("returns src unchanged when prefix is empty", () => {
      const src = "/carte/x/?sc_id=1"
      expect(
        injectLocationIntoSrc(src, "", {
          adresse: null,
          latitude: "47.66",
          longitude: "-2.99",
        }),
      ).toBe(src)
    })
  })
})
