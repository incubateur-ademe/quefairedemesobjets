import { addressElement, pinpointElement } from "../js/assistant/pinpoint"

const colors = { geste: "#00f", bonus: "#0a0", address: "#f00" }
const place = { uuid: "a", nom: "Atelier", longitude: 0, latitude: 0, bonus: true }

describe("assistant pinpoints", () => {
  it("the bonus pastille shows on the réparer map, in the bonus colour", () => {
    const element = pinpointElement(place, colors, "reparer")

    expect(element.querySelector(".qfa-pinpoint__bonus")).not.toBeNull()
    expect(element.style.getPropertyValue("--qfa-pinpoint-color")).toBe("#0a0")
  })

  it("a repairer's bonus stays off the other gestes' maps", () => {
    const element = pinpointElement(place, colors, "donner_echanger_rapporter")

    expect(element.querySelector(".qfa-pinpoint__bonus")).toBeNull()
    expect(element.style.getPropertyValue("--qfa-pinpoint-color")).toBe("#00f")
  })

  it("a pin is a link to the place page when there is one, a button otherwise", () => {
    const link = pinpointElement(place, colors, "trier", (uuid) => `/lieu/${uuid}/`)
    const button = pinpointElement(place, colors, "trier")

    expect(link.tagName).toBe("A")
    expect(link.getAttribute("href")).toBe("/lieu/a/")
    expect(button.tagName).toBe("BUTTON")
    expect(button.getAttribute("aria-label")).toBe("Atelier")
  })

  it("the address marker is an image in the address colour", () => {
    const element = addressElement(colors)

    expect(element.getAttribute("role")).toBe("img")
    expect(element.style.getPropertyValue("--qfa-pinpoint-color")).toBe("#f00")
  })
})
