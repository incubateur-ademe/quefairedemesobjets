import { Controller } from "@hotwired/stimulus"

const REVERSE_GEOCODE_URL =
  "https://data.geopf.fr/geocodage/reverse/?lon={lon}&lat={lat}"

interface CommitDetail {
  option: HTMLElement
  value: string
  selectedValue: string
}

interface AddressChangeDetail {
  adresse: string
  latitude: string
  longitude: string
}

export default class CarteAddressAutocompleteController extends Controller<HTMLElement> {
  static targets = ["input", "latitude", "longitude", "displayError"]

  declare readonly inputTarget: HTMLInputElement
  declare readonly latitudeTarget: HTMLInputElement
  declare readonly longitudeTarget: HTMLInputElement
  declare readonly displayErrorTarget: HTMLElement
  declare readonly hasDisplayErrorTarget: boolean

  commit(event: CustomEvent<CommitDetail>) {
    const option = event.detail.option
    const label = event.detail.selectedValue

    if (option.dataset.geolocate === "true") {
      this.#triggerGeolocation()
      return
    }

    const latitude = option.dataset.lat ?? ""
    const longitude = option.dataset.lon ?? ""
    this.#setLocation({ adresse: label, latitude, longitude })
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
    const url = REVERSE_GEOCODE_URL.replace(
      "{lon}",
      position.coords.longitude.toString(),
    ).replace("{lat}", position.coords.latitude.toString())
    try {
      const response = await fetch(url)
      const data = await response.json()
      if (!data.features?.length) {
        this.#displayInputError(
          "Votre adresse n'a pas pu être déterminée. Vous pouvez ré-essayer ou saisir votre adresse manuellement",
        )
        return
      }
      const feature = data.features[0]
      this.#setLocation({
        adresse: feature.properties.label,
        latitude: feature.geometry.coordinates[1].toString(),
        longitude: feature.geometry.coordinates[0].toString(),
      })
    } catch (error) {
      console.error("reverse geocoding failed:", error)
      this.#displayInputError(
        "Votre adresse n'a pas pu être déterminée. Vous pouvez ré-essayer ou saisir votre adresse manuellement",
      )
    }
  }

  #setLocation(detail: AddressChangeDetail) {
    this.inputTarget.value = detail.adresse
    this.latitudeTarget.value = detail.latitude
    this.longitudeTarget.value = detail.longitude
    this.#hideInputError()
    this.dispatch("change", { detail })
  }

  #displayInputError(message: string) {
    this.inputTarget.classList.add("fr-input--error")
    this.inputTarget.parentElement?.classList.add("fr-input-group--error")
    if (this.hasDisplayErrorTarget) {
      this.displayErrorTarget.innerHTML = message
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
