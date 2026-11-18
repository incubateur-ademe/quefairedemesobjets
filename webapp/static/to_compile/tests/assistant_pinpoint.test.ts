import { addressElement, pinpointElement } from "../js/assistant/pinpoint"

const colors = { bonus: "#0a0", address: "#f00" }
const place = {
  uuid: "a",
  nom: "Atelier",
  longitude: 0,
  latitude: 0,
  bonus: true,
  geste: "reparer",
}

describe("assistant pinpoints", () => {
  it("the bonus pastille shows on a réparer pin, in the bonus colour", () => {
    const element = pinpointElement(place, colors, "reparer")

    expect(element.querySelector(".qfa-pinpoint__bonus")).not.toBeNull()
    expect(element.style.getPropertyValue("--qfa-pinpoint-color")).toBe("#0a0")
  })

  it("another geste's pin takes its colour from its geste, without the bonus", () => {
    const element = pinpointElement(place, colors, "donner_echanger_rapporter")

    expect(element.dataset.geste).toBe("donner_echanger_rapporter")
    expect(element.querySelector(".qfa-pinpoint__bonus")).toBeNull()
    expect(element.style.getPropertyValue("--qfa-pinpoint-color")).toBe("")
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
