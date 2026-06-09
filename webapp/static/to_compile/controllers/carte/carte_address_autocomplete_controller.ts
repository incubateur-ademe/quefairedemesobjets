import { Controller } from "@hotwired/stimulus"

interface LocationDetail {
  adresse: string
  latitude: string
  longitude: string
}

interface NextAutocompleteCommitDetail {
  option: HTMLElement
  value: string
  selectedValue: string
}

/**
 * Carte-specific listener that turns a `next-autocomplete:commit` event into
 * lat/lon population on the surrounding form and dispatches the
 * `carte-address-autocomplete:change` event that the global state controller
 * listens to.
 *
 * Also handles the synthetic « Autour de moi » option by triggering
 * `navigator.geolocation` and calling the server-side BAN reverse-geocode
 * proxy (see qfdmo.views.autocomplete.ReverseGeocodeBanView). The browser
 * never talks to data.geopf.fr directly — the proxy keeps a single
 * server-side timeout and cache policy and avoids CORS coupling.
 *
 * The combobox plumbing (search, listbox, keyboard nav, commit) belongs to the
 * inner `next-autocomplete` controller mounted by the widget itself. This
 * controller is mounted on the outer wrapper so it can reach the lat/lon
 * sibling inputs as Stimulus targets.
 */
export default class CarteAddressAutocompleteController extends Controller<HTMLElement> {
  static targets = ["input", "latitude", "longitude", "displayError"]
  static values = {
    reverseGeocodeUrl: String,
  }

  declare readonly inputTarget: HTMLInputElement
  declare readonly latitudeTarget: HTMLInputElement
  declare readonly longitudeTarget: HTMLInputElement
  declare readonly displayErrorTarget: HTMLElement
  declare readonly hasDisplayErrorTarget: boolean
  declare readonly reverseGeocodeUrlValue: string

  commit(event: CustomEvent<NextAutocompleteCommitDetail>) {
    const option = event.detail.option
    if (!option) return

    if (option.dataset.geolocate === "true") {
      this.#triggerGeolocation()
      return
    }

    this.#setLocation({
      adresse: option.dataset.selectedValue?.trim() ?? "",
      latitude: option.dataset.lat ?? "",
      longitude: option.dataset.lon ?? "",
    })
  }

  #triggerGeolocation() {
    if (!("geolocation" in navigator)) {
      this.#displayInputError("La géolocalisation est inaccessible sur votre appareil")
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) => this.#reverseGeocode(position),
      () =>
        this.#displayInputError(
          "La géolocalisation est inaccessible sur votre appareil",
        ),
    )
  }

  async #reverseGeocode(position: GeolocationPosition) {
    const url = new URL(this.reverseGeocodeUrlValue, window.location.origin)
    url.searchParams.set("lat", position.coords.latitude.toString())
    url.searchParams.set("lon", position.coords.longitude.toString())
    try {
      const response = await fetch(url.toString())
      if (!response.ok) {
        this.#displayInputError(
          "Votre adresse n'a pas pu être déterminée. Vous pouvez ré-essayer ou saisir votre adresse manuellement",
        )
        return
      }
      const data = await response.json()
      if (!data.adresse) {
        this.#displayInputError(
          "Votre adresse n'a pas pu être déterminée. Vous pouvez ré-essayer ou saisir votre adresse manuellement",
        )
        return
      }
      this.#setLocation({
        adresse: data.adresse,
        latitude: data.latitude.toString(),
        longitude: data.longitude.toString(),
      })
    } catch (error) {
      console.error("reverse geocoding failed:", error)
      this.#displayInputError(
        "Votre adresse n'a pas pu être déterminée. Vous pouvez ré-essayer ou saisir votre adresse manuellement",
      )
    }
  }

  #setLocation(detail: LocationDetail) {
    this.inputTarget.value = detail.adresse
    this.latitudeTarget.value = detail.latitude
    this.longitudeTarget.value = detail.longitude
    this.#hideInputError()
    // `carte-address-autocomplete:change` is consumed by the page-level
    // `location` controller (body data-action -> location#persistAndBroadcast),
    // which persists the location and re-emits a document-level
    // `qf:location-changed` event that each carte form submits itself on.
    this.dispatch("change", { detail })
  }

  #displayInputError(message: string) {
    this.inputTarget.classList.add("fr-input--error")
    this.inputTarget.parentElement?.classList.add("fr-input-group--error")
    if (this.hasDisplayErrorTarget) {
      this.displayErrorTarget.textContent = message
      this.displayErrorTarget.style.display = "block"
    }
    this.inputTarget.value = ""
    this.latitudeTarget.value = ""
    this.longitudeTarget.value = ""
  }

  #hideInputError() {
    this.inputTarget.classList.remove("fr-input--error")
    this.inputTarget.parentElement?.classList.remove("fr-input-group--error")
    if (this.hasDisplayErrorTarget) {
      this.displayErrorTarget.style.display = "none"
    }
  }
}
