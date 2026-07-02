import "@testing-library/jest-dom"

import { Application } from "@hotwired/stimulus"
import FrameLocationController from "../controllers/carte/frame_location_controller"

const PREFIX = "tous-les-gestes_map"

function setupFrame(src: string | null) {
  const srcAttr = src === null ? "" : `src="${src}"`
  document.body.innerHTML = `<turbo-frame
    id="tous-les-gestes"
    loading="lazy"
    data-controller="frame-location"
    data-frame-location-prefix-value="${PREFIX}"
    ${srcAttr}></turbo-frame>`
  return document.querySelector("turbo-frame") as HTMLElement
}

let app: Application | undefined

function startStimulus() {
  app = Application.start()
  app.register("frame-location", FrameLocationController)
  return app
}

async function flush() {
  await new Promise((r) => setTimeout(r, 0))
}

describe("FrameLocationController", () => {
  beforeEach(() => {
    sessionStorage.clear()
    document.body.innerHTML = ""
  })

  afterEach(() => {
    app?.stop()
    app = undefined
  })

  it("injects the stored location into src and strips loading=lazy on connect", async () => {
    sessionStorage.setItem("latitude", "47.66")
    sessionStorage.setItem("longitude", "-2.99")
    sessionStorage.setItem("adresse", "Auray")

    const frame = setupFrame("/carte/tous-les-gestes/?sc_id=88")
    startStimulus()
    await flush()

    const url = new URL(frame.getAttribute("src")!, "https://example.test")
    expect(url.searchParams.get("sc_id")).toBe("88")
    expect(url.searchParams.get(`${PREFIX}-latitude`)).toBe("47.66")
    expect(url.searchParams.get(`${PREFIX}-longitude`)).toBe("-2.99")
    expect(url.searchParams.get(`${PREFIX}-adresse`)).toBe("Auray")
    expect(frame.hasAttribute("loading")).toBe(false)
  })

  it("leaves src unchanged when no location is stored", async () => {
    const frame = setupFrame("/carte/tous-les-gestes/?sc_id=88")
    startStimulus()
    await flush()

    expect(frame.getAttribute("src")).toBe("/carte/tous-les-gestes/?sc_id=88")
  })

  it("does nothing when src is missing", async () => {
    sessionStorage.setItem("latitude", "47.66")
    sessionStorage.setItem("longitude", "-2.99")

    const frame = setupFrame(null)
    startStimulus()
    await flush()

    expect(frame.hasAttribute("src")).toBe(false)
  })
})
