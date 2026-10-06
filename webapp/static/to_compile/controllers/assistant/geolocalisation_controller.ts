import { Controller } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

/** The label the address field shows when the street could not be found. */
const FALLBACK_ADDRESS = "Autour de moi"
/** Shown while the browser asks for consent (Figma 30495:10893). */
const LOCATING_LABEL = "Localisation en cours ..."

/**
 * "Je découvre les solutions près de moi": the fiche was reached without an
 * address (Figma 30495:2279).
 *
 * The click asks the browser for the user's position, names it through the
 * BAN reverse-geocode proxy, and opens the solutions screen there. Whatever
 * fails along the way, the link is still followed: the solutions screen
 * without a position centers on a default view, and its address field lets
 * the user type one.
 */
export default class extends Controller<HTMLAnchorElement> {
  static targets = ["libelle"]
  static values = { reverseGeocodeUrl: String }

  declare readonly libelleTarget: HTMLElement
  declare reverseGeocodeUrlValue: string

  private locating = false
  private label = ""

  locate(event: MouseEvent) {
    // Modified clicks (new tab, new window) keep the plain link.
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return
    if (!("geolocation" in navigator)) return
    event.preventDefault()
    if (this.locating) return
    this.locating = true
    // `aria-busy` also switches the pin to the spinner, in the stylesheet.
    this.element.setAttribute("aria-busy", "true")
    this.label = this.libelleTarget.textContent ?? ""
    this.libelleTarget.textContent = LOCATING_LABEL

    navigator.geolocation.getCurrentPosition(
      (position) => void this.#visitAround(position.coords),
      () => this.#visit(this.element.href),
    )
  }

  async #visitAround({ latitude, longitude }: GeolocationCoordinates) {
    const url = new URL(this.element.href)
    url.searchParams.set("adresse", await this.#addressOf(latitude, longitude))
    url.searchParams.set("longitude", String(longitude))
    url.searchParams.set("latitude", String(latitude))
    // A device position is a point, not a municipality: the map shows it.
    url.searchParams.set("precise", "true")
    this.#visit(url.toString())
  }

  async #addressOf(latitude: number, longitude: number): Promise<string> {
    const url = new URL(this.reverseGeocodeUrlValue, window.location.origin)
    url.searchParams.set("lat", String(latitude))
    url.searchParams.set("lon", String(longitude))
    try {
      const response = await fetch(url)
      if (!response.ok) return FALLBACK_ADDRESS
      const { adresse } = (await response.json()) as { adresse?: string }
      return adresse || FALLBACK_ADDRESS
    } catch {
      // The coordinates are enough to search: only the label is lost.
      return FALLBACK_ADDRESS
    }
  }

  #visit(url: string) {
    // Restored before leaving: going back must not find a button stuck loading.
    this.locating = false
    this.element.removeAttribute("aria-busy")
    this.libelleTarget.textContent = this.label
    Turbo.visit(url)
  }
}
