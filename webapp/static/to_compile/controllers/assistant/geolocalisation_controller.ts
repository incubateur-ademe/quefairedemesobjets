import { Controller } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

const FALLBACK_ADDRESS = "Autour de moi"
const LOCATING_LABEL = "Localisation en cours ..."
const POSITION_OPTIONS: PositionOptions = { timeout: 10_000, maximumAge: 60_000 }

/**
 * Opens the solutions around the user's position, named through the BAN
 * reverse geocoder. Whatever fails, the link is still followed: the solutions
 * screen then asks for an address.
 */
export default class extends Controller<HTMLAnchorElement> {
  static targets = ["libelle"]
  static values = { reverseGeocodeUrl: String }

  declare readonly libelleTarget: HTMLElement
  declare reverseGeocodeUrlValue: string

  #locating = false
  #label = ""

  locate(event: MouseEvent) {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return
    if (!("geolocation" in navigator)) return
    event.preventDefault()
    if (this.#locating) return
    this.#locating = true
    this.element.setAttribute("aria-busy", "true")
    this.#label = this.libelleTarget.textContent ?? ""
    this.libelleTarget.textContent = LOCATING_LABEL

    navigator.geolocation.getCurrentPosition(
      (position) => void this.#visitAround(position.coords),
      () => this.#visit(this.element.href),
      POSITION_OPTIONS,
    )
  }

  async #visitAround({ latitude, longitude }: GeolocationCoordinates) {
    const url = new URL(this.element.href)
    url.searchParams.set("adresse", await this.#addressOf(latitude, longitude))
    url.searchParams.set("longitude", String(longitude))
    url.searchParams.set("latitude", String(latitude))
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
      return FALLBACK_ADDRESS
    }
  }

  #visit(url: string) {
    // Restored before leaving, for the back button.
    this.#locating = false
    this.element.removeAttribute("aria-busy")
    this.libelleTarget.textContent = this.#label
    Turbo.visit(url)
  }
}
