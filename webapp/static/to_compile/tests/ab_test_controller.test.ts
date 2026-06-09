import "@testing-library/jest-dom"

import { Application } from "@hotwired/stimulus"
import AbTestController from "../controllers/shared/ab_test_controller"

const onFeatureFlags = jest.fn()
const getFeatureFlag = jest.fn()
const register = jest.fn()

jest.mock("posthog-js", () => ({
  __esModule: true,
  default: {
    onFeatureFlags: (cb: () => void) => onFeatureFlags(cb),
    getFeatureFlag: (key: string) => getFeatureFlag(key),
    register: (props: Record<string, unknown>) => register(props),
  },
}))

const CONTROL_SRC = "/carte/foo?a=1"
const VARIANT_SRC = "/carte/foo?a=1&view_mode-view=liste"
const FLAG_KEY = "produit-carte-default-view-mobile"

function setupFrame(extraAttrs: Record<string, string> = {}) {
  const attrs = {
    "data-controller": "ab-test",
    "data-ab-test-flag-key-value": FLAG_KEY,
    "data-ab-test-src-variant-value": VARIANT_SRC,
    src: CONTROL_SRC,
    ...extraAttrs,
  }
  const attrString = Object.entries(attrs)
    .map(([k, v]) => `${k}="${v}"`)
    .join(" ")
  document.body.innerHTML = `<turbo-frame id="carte" ${attrString}></turbo-frame>`
  return document.querySelector("turbo-frame") as HTMLElement
}

let app: Application | undefined

function startStimulus() {
  app = Application.start()
  app.register("ab-test", AbTestController)
  return app
}

function setMobileViewport(isMobile: boolean) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: jest.fn().mockReturnValue({ matches: isMobile }),
  })
}

async function flush() {
  await new Promise((r) => setTimeout(r, 0))
}

describe("AbTestController", () => {
  beforeEach(() => {
    onFeatureFlags.mockReset().mockImplementation((cb: () => void) => cb())
    getFeatureFlag.mockReset()
    register.mockReset()
    setMobileViewport(true)
    sessionStorage.clear()
  })

  afterEach(() => {
    app?.stop()
    app = undefined
  })

  it("assigns variant src when flag returns 'test' on mobile", async () => {
    getFeatureFlag.mockReturnValue("test")
    const frame = setupFrame()
    startStimulus()
    await flush()

    expect(frame.getAttribute("src")).toBe(VARIANT_SRC)
    expect(register).toHaveBeenCalledWith({ [`$feature/${FLAG_KEY}`]: "test" })
  })

  it("restores control src when flag returns 'control'", async () => {
    getFeatureFlag.mockReturnValue("control")
    const frame = setupFrame()
    startStimulus()
    await flush()

    expect(frame.getAttribute("src")).toBe(CONTROL_SRC)
  })

  it("restores control src when flag is missing/undefined", async () => {
    getFeatureFlag.mockReturnValue(undefined)
    const frame = setupFrame()
    startStimulus()
    await flush()

    expect(frame.getAttribute("src")).toBe(CONTROL_SRC)
  })

  it("forces control on desktop viewport even when flag returns 'test'", async () => {
    setMobileViewport(false)
    getFeatureFlag.mockReturnValue("test")
    const frame = setupFrame({ "data-ab-test-mobile-only-value": "true" })
    startStimulus()
    await flush()

    expect(frame.getAttribute("src")).toBe(CONTROL_SRC)
    // PostHog flag is never read, so no registration on desktop.
    expect(getFeatureFlag).not.toHaveBeenCalled()
  })

  it("honours variant on desktop when mobileOnly is false", async () => {
    setMobileViewport(false)
    getFeatureFlag.mockReturnValue("test")
    const frame = setupFrame({ "data-ab-test-mobile-only-value": "false" })
    startStimulus()
    await flush()

    expect(frame.getAttribute("src")).toBe(VARIANT_SRC)
  })

  it("falls back to control when getFeatureFlag throws", async () => {
    getFeatureFlag.mockImplementation(() => {
      throw new Error("boom")
    })
    const frame = setupFrame()
    startStimulus()
    await flush()

    expect(frame.getAttribute("src")).toBe(CONTROL_SRC)
  })

  it("falls back to control when onFeatureFlags throws", async () => {
    onFeatureFlags.mockImplementation(() => {
      throw new Error("posthog not ready")
    })
    const frame = setupFrame()
    startStimulus()
    await flush()

    expect(frame.getAttribute("src")).toBe(CONTROL_SRC)
  })

  describe("location injection from sessionStorage", () => {
    const PREFIX = "foo"

    function seedLocation() {
      sessionStorage.setItem("latitude", "47.66")
      sessionStorage.setItem("longitude", "-2.99")
      sessionStorage.setItem("adresse", "Auray")
    }

    it("bakes stored location into the variant src (test cohort)", async () => {
      seedLocation()
      getFeatureFlag.mockReturnValue("test")
      const frame = setupFrame({ "data-ab-test-prefix-value": `${PREFIX}_map` })
      startStimulus()
      await flush()

      const url = new URL(frame.getAttribute("src")!, "https://example.test")
      expect(url.searchParams.get("view_mode-view")).toBe("liste") // still variant
      expect(url.searchParams.get(`${PREFIX}_map-latitude`)).toBe("47.66")
      expect(url.searchParams.get(`${PREFIX}_map-longitude`)).toBe("-2.99")
    })

    it("bakes stored location into the control src", async () => {
      seedLocation()
      getFeatureFlag.mockReturnValue("control")
      const frame = setupFrame({ "data-ab-test-prefix-value": `${PREFIX}_map` })
      startStimulus()
      await flush()

      const url = new URL(frame.getAttribute("src")!, "https://example.test")
      expect(url.searchParams.has("view_mode-view")).toBe(false) // control
      expect(url.searchParams.get(`${PREFIX}_map-latitude`)).toBe("47.66")
    })

    it("bakes location into control src on desktop (mobileOnly bypass)", async () => {
      seedLocation()
      setMobileViewport(false)
      getFeatureFlag.mockReturnValue("test")
      const frame = setupFrame({
        "data-ab-test-mobile-only-value": "true",
        "data-ab-test-prefix-value": `${PREFIX}_map`,
      })
      startStimulus()
      await flush()

      const url = new URL(frame.getAttribute("src")!, "https://example.test")
      expect(url.searchParams.has("view_mode-view")).toBe(false)
      expect(url.searchParams.get(`${PREFIX}_map-latitude`)).toBe("47.66")
    })

    it("captures a location written during the async PostHog window", async () => {
      // Simulate the user picking an address while PostHog is still resolving:
      // sessionStorage is written inside the onFeatureFlags callback, BEFORE the
      // flag callback runs. Injection reads at #assign time, so it must be seen.
      onFeatureFlags.mockImplementation((cb: () => void) => {
        seedLocation()
        cb()
      })
      getFeatureFlag.mockReturnValue("test")
      const frame = setupFrame({ "data-ab-test-prefix-value": `${PREFIX}_map` })
      startStimulus()
      await flush()

      const url = new URL(frame.getAttribute("src")!, "https://example.test")
      expect(url.searchParams.get(`${PREFIX}_map-latitude`)).toBe("47.66")
    })

    it("leaves src untouched when sessionStorage has no location", async () => {
      getFeatureFlag.mockReturnValue("test")
      const frame = setupFrame({ "data-ab-test-prefix-value": `${PREFIX}_map` })
      startStimulus()
      await flush()

      expect(frame.getAttribute("src")).toBe(VARIANT_SRC)
    })
  })

  it("does nothing when src attribute is missing", async () => {
    document.body.innerHTML = `<turbo-frame
      id="carte"
      data-controller="ab-test"
      data-ab-test-flag-key-value="${FLAG_KEY}"
      data-ab-test-src-variant-value="${VARIANT_SRC}"></turbo-frame>`
    startStimulus()
    await flush()

    const frame = document.querySelector("turbo-frame") as HTMLElement
    expect(frame.hasAttribute("src")).toBe(false)
    expect(getFeatureFlag).not.toHaveBeenCalled()
  })
})
