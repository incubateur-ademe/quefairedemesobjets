import type { Place } from "./visible_places"

export type PinpointColors = {
  geste: string
  bonus: string
  address: string
}

/**
 * DOM element of a pinpoint.
 *
 * The color follows the geste chosen by the user, not a property of the
 * place: the same acteur shows in blue if the user chose "donner" and in brown
 * if they chose "revendre" (#3295). Only the Bonus Réparation is an exception
 * and overrides the geste color.
 */
export function pinpointElement(
  place: Place,
  colors: PinpointColors,
  geste: string,
  lieuUrl?: (uuid: string) => string,
): HTMLElement {
  // A link when a place page exists (openable in a new tab, usable without
  // JavaScript) and a button otherwise: an `<a>` without `href` is neither
  // focusable nor announced, while a button stays keyboard-accessible even
  // before the place page is delivered.
  const element = lieuUrl
    ? Object.assign(document.createElement("a"), { href: lieuUrl(place.uuid) })
    : Object.assign(document.createElement("button"), { type: "button" })
  element.className = "qfa-pinpoint"
  element.dataset.uuid = place.uuid
  element.dataset.geste = geste
  element.setAttribute("aria-label", place.nom)
  element.style.setProperty(
    "--qfa-pinpoint-color",
    place.bonus ? colors.bonus : colors.geste,
  )
  if (place.bonus) element.dataset.bonus = "true"

  const icon = document.createElement("span")
  icon.className = "qfa-pinpoint__icon"
  element.append(icon)
  return element
}

/**
 * Marker of the address entered by the user.
 *
 * Only created for a precise address, never for a municipality (#3356):
 * "Lyon" has no position to show.
 */
export function addressElement(colors: PinpointColors): HTMLElement {
  const element = document.createElement("div")
  element.className = "qfa-pinpoint qfa-pinpoint--address"
  element.setAttribute("role", "img")
  element.setAttribute("aria-label", "Votre adresse")
  element.style.setProperty("--qfa-pinpoint-color", colors.address)
  return element
}
