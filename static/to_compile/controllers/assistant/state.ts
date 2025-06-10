import { Controller } from "@hotwired/stimulus"
import AdresseAutocompleteController from "../carte/address_autocomplete_controller"
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
    // Checker l'id de la turbo frame dans le callback
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
      this.persistInSessionStorageIfChanged(value.adresse, "adresse")
      this.persistInSessionStorageIfChanged(value.latitude, "latitude")
      this.persistInSessionStorageIfChanged(value.longitude, "longitude")
    }

    for (const outlet of this.addressAutocompleteOutlets) {
      if (value.adresse && value.adresse !== outlet.inputTarget.value) {
        outlet.inputTarget.value = value.adresse
      }
      if (value.latitude && outlet.latitudeTarget.value !== value.latitude) {
        outlet.latitudeTarget.value = value.latitude
      }
      if (value.longitude && outlet.longitudeTarget.value !== value.longitude) {
        outlet.longitudeTarget.value = value.longitude
      }
    }

    this.submit()
  }

  submit() {
    for (const outlet of this.searchSolutionFormOutlets) {
      outlet.advancedSubmit()
    }
  }

  updateBbox(event) {
    for (const outlet of this.searchSolutionFormOutlets) {
      outlet.updateBboxInput(event)
    }
  }

  persistInSessionStorageIfChanged(value, key) {
    if (value !== sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, value)
    }
  }
}


