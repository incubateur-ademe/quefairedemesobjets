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

function startStimulus() {
  const application = Application.start()
  application.register("ab-test", AbTestController)
  return application
}

async function flush() {
  await new Promise((r) => setTimeout(r, 0))
}

describe("AbTestController", () => {
  beforeEach(() => {
    onFeatureFlags.mockReset().mockImplementation((cb: () => void) => cb())
    getFeatureFlag.mockReset()
    register.mockReset()
  })

  it("assigns variant src when flag returns 'test'", async () => {
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
