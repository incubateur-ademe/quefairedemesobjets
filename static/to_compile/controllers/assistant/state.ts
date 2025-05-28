import { Controller } from "@hotwired/stimulus"
import AdresseAutocompleteController from "../carte/address_autocomplete_controller"
import MapController from "../carte/map_controller"
import SearchFormController from "../carte/search_solution_form_controller"

export default class extends Controller<HTMLElement> {
  static values = {
    "location": Object
  }
  static outlets = ["address-autocomplete", "search-solution-form"]
  declare addressAutocompleteOutlets: Array<AdresseAutocompleteController>
  declare searchSolutionFormOutlets: Array<SearchFormController>
  declare locationValue: { adresse: string | null, latitude: string | null, longitude: string | null }

  connect() {
    this.element.addEventListener("turbo:frame-load", this.fetchLocationFromSessionStorage.bind(this))
  }

  fetchLocationFromSessionStorage() {
    const nextLocationValue = {
      "adresse": sessionStorage.getItem("adresse"),
      "latitude": sessionStorage.getItem("latitude"),
      "longitude": sessionStorage.getItem("longitude")
    }

    if (Object.values(nextLocationValue).find(value => !!value)) {
      this.locationValue = nextLocationValue
    }
  }

  setLocation(event) {
    this.locationValue = event.detail
  }

  locationValueChanged(value, previousValue) {
    if (value && previousValue) {
      this.#persistInSessionStorageIfChanged(value.adresse, "adresse")
      this.#persistInSessionStorageIfChanged(value.latitude, "latitude")
      this.#persistInSessionStorageIfChanged(value.longitude, "longitude")
    }

    for (const outlet of this.addressAutocompleteOutlets) {
      console.log("fill form", { outlet })
      outlet.inputTarget.value = value.adresse
      outlet.latitudeTarget.value = value.latitude
      outlet.longitudeTarget.value = value.longitude
    }

    for (const outlet of this.searchSolutionFormOutlets) {
      console.log("submit", { outlet })
      outlet.advancedSubmit()
    }
  }

  #persistInSessionStorageIfChanged(value, key) {
    if (value !== sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, value)
    }
  }
}


