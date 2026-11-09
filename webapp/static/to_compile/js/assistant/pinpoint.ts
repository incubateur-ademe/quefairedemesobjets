import type { Place } from "./visible_places"

export type PinpointColors = {
  geste: string
  bonus: string
  address: string
}

/**
 * DOM element of a pinpoint, in the colour of the geste chosen; the Bonus
 * Réparation colour overrides it on the "réparer" map only.
 */
export function pinpointElement(
  place: Place,
  colors: PinpointColors,
  geste: string,
  lieuUrl?: (uuid: string) => string,
): HTMLElement {
  // A button when there is no place page: an `<a>` without `href` is neither
  // focusable nor announced.
  const element = lieuUrl
    ? Object.assign(document.createElement("a"), { href: lieuUrl(place.uuid) })
    : Object.assign(document.createElement("button"), { type: "button" })
  element.className = "qfa-pinpoint"
  element.dataset.uuid = place.uuid
  element.dataset.geste = geste
  element.setAttribute("aria-label", place.nom)
  const hasBonus = place.bonus && geste === "reparer"
  element.style.setProperty(
    "--qfa-pinpoint-color",
    hasBonus ? colors.bonus : colors.geste,
  )
  if (hasBonus) element.dataset.bonus = "true"

  const icon = document.createElement("span")
  icon.className = "qfa-pinpoint__icon"
  element.append(icon)

  if (hasBonus) {
    const pastille = document.createElement("span")
    pastille.className = "qfa-pinpoint__bonus"
    element.append(pastille)
  }
  return element
}

/** Marker of the precise address entered by the user. */
export function addressElement(colors: PinpointColors): HTMLElement {
  const element = document.createElement("div")
  element.className = "qfa-pinpoint qfa-pinpoint--address"
  element.setAttribute("role", "img")
  element.setAttribute("aria-label", "Votre adresse")
  element.style.setProperty("--qfa-pinpoint-color", colors.address)
  return element
}
