import "@testing-library/jest-dom"

import { Application } from "@hotwired/stimulus"
import LocationController, {
  LOCATION_CHANGED_EVENT,
} from "../controllers/shared/location_controller"

let app: Application | undefined

function startStimulus() {
  app = Application.start()
  app.register("location", LocationController)
  return app
}

async function flush() {
  await new Promise((r) => setTimeout(r, 0))
}

function captureLocationEvents(): Array<CustomEvent> {
  const events: Array<CustomEvent> = []
  document.addEventListener(LOCATION_CHANGED_EVENT, (e) =>
    events.push(e as CustomEvent),
  )
  return events
}

describe("LocationController", () => {
  beforeEach(() => {
    sessionStorage.clear()
    document.body.innerHTML = ""
    document.body.removeAttribute("data-action")
    document.body.setAttribute("data-controller", "location")
    document.body.setAttribute(
      "data-action",
      "carte-address-autocomplete:change->location#persistAndBroadcast " +
        "address-autocomplete:change->location#persistAndBroadcast",
    )
  })

  afterEach(() => {
    app?.stop()
    app = undefined
  })

  it("persists the picked location and emits qf:location-changed", async () => {
    const events = captureLocationEvents()
    startStimulus()
    await flush()

    const detail = { adresse: "Auray", latitude: "47.66", longitude: "-2.99" }
    document.body.dispatchEvent(
      new CustomEvent("carte-address-autocomplete:change", {
        detail,
        bubbles: true,
      }),
    )

    expect(sessionStorage.getItem("adresse")).toBe("Auray")
    expect(sessionStorage.getItem("latitude")).toBe("47.66")
    expect(sessionStorage.getItem("longitude")).toBe("-2.99")
    expect(events).toHaveLength(1)
    expect(events[0].detail).toEqual(detail)
  })

  it("also reacts to address-autocomplete:change (formulaire widget)", async () => {
    const events = captureLocationEvents()
    startStimulus()
    await flush()

    document.body.dispatchEvent(
      new CustomEvent("address-autocomplete:change", {
        detail: { adresse: "Nantes", latitude: "47.21", longitude: "-1.55" },
        bubbles: true,
      }),
    )

    expect(events).toHaveLength(1)
    expect(sessionStorage.getItem("latitude")).toBe("47.21")
  })

  it("ignores an event without detail", async () => {
    const events = captureLocationEvents()
    startStimulus()
    await flush()

    document.body.dispatchEvent(
      new CustomEvent("carte-address-autocomplete:change", { bubbles: true }),
    )

    expect(events).toHaveLength(0)
  })
})
