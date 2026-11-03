import { Application } from "@hotwired/stimulus"
import GeolocalisationController from "../controllers/assistant/geolocalisation_controller"

jest.mock("@hotwired/turbo", () => ({ visit: jest.fn() }))
const visit = (jest.requireMock("@hotwired/turbo") as { visit: jest.Mock }).visit

const HREF = "http://localhost/assistant/solutions/?geste=reparer"
const settle = () => new Promise((resolve) => setTimeout(resolve, 0))

let application: Application
let getCurrentPosition: jest.Mock

beforeEach(async () => {
  document.body.innerHTML = `
    <a href="${HREF}" data-controller="assistant-geolocalisation"
       data-assistant-geolocalisation-reverse-geocode-url-value="/reverse"
       data-action="click->assistant-geolocalisation#locate">
      <span data-assistant-geolocalisation-target="libelle">Près de moi</span>
    </a>`
  getCurrentPosition = jest.fn()
  Object.defineProperty(navigator, "geolocation", {
    value: { getCurrentPosition },
    configurable: true,
  })
  global.fetch = jest.fn(async () => ({
    ok: true,
    json: async () => ({ adresse: "12 rue de la Paix" }),
  })) as unknown as typeof fetch
  visit.mockClear()
  application = Application.start()
  application.register("assistant-geolocalisation", GeolocalisationController)
  await settle()
})

afterEach(() => application.stop())

const link = () => document.querySelector("a") as HTMLAnchorElement

describe("assistant geolocalisation", () => {
  it("asks for the position with a timeout and shows it is busy", () => {
    link().click()

    expect(getCurrentPosition.mock.calls[0][2]).toMatchObject({ timeout: 10_000 })
    expect(link().getAttribute("aria-busy")).toBe("true")
  })

  it("opens the solutions around the position, named and precise", async () => {
    getCurrentPosition.mockImplementation((success) =>
      success({ coords: { latitude: 48.85, longitude: 2.35 } }),
    )

    link().click()
    await settle()
    await settle()

    const url = new URL(visit.mock.calls[0][0])
    expect(url.searchParams.get("adresse")).toBe("12 rue de la Paix")
    expect(url.searchParams.get("longitude")).toBe("2.35")
    expect(url.searchParams.get("precise")).toBe("true")
    expect(link().hasAttribute("aria-busy")).toBe(false)
  })

  it("follows the link when the position is refused", () => {
    getCurrentPosition.mockImplementation((_success, error) => error())

    link().click()

    expect(visit).toHaveBeenCalledWith(HREF)
    expect(link().textContent?.trim()).toBe("Près de moi")
  })

  it("leaves a modified click to the browser", () => {
    link().dispatchEvent(
      new MouseEvent("click", { bubbles: true, cancelable: true, metaKey: true }),
    )

    expect(getCurrentPosition).not.toHaveBeenCalled()
  })
})
