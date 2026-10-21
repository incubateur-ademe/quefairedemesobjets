import { pinpointElement } from "../js/assistant/pinpoint"

const colors = { geste: "#00f", bonus: "#0a0", address: "#f00" }
const place = { uuid: "a", nom: "Atelier", longitude: 0, latitude: 0, bonus: true }

test("the bonus pastille shows on the réparer map", () => {
  const element = pinpointElement(place, colors, "reparer")

  expect(element.querySelector(".qfa-pinpoint__bonus")).not.toBeNull()
})

test("a repairer's bonus stays off the other gestes' maps", () => {
  const element = pinpointElement(place, colors, "donner_echanger_rapporter")

  expect(element.querySelector(".qfa-pinpoint__bonus")).toBeNull()
  expect(element.style.getPropertyValue("--qfa-pinpoint-color")).toBe("#00f")
})
