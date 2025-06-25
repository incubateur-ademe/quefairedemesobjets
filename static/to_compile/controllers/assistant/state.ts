import { Controller } from "@hotwired/stimulus"
import isEmpty from "lodash/isEmpty"
import AdresseAutocompleteController from "../carte/address_autocomplete_controller"
import SearchFormController from "../carte/search_solution_form_controller"

export default class extends Controller<HTMLElement> {
  static values = {
    location: Object,
  }
  static outlets = ["address-autocomplete", "search-solution-form"]
  declare addressAutocompleteOutlets: Array<AdresseAutocompleteController>
  declare searchSolutionFormOutlets: Array<SearchFormController>
  declare locationValue: {
    adresse: string | null
    latitude: string | null
    longitude: string | null
  }

  connect() {
    document.addEventListener(
      "turbo:frame-load",
      this.fetchLocationFromSessionStorageOnFirstLoad.bind(this),
    )
  }

  fetchLocationFromSessionStorageOnFirstLoad(event) {
    if (!isEmpty(this.locationValue)) {
      document.removeEventListener(
        "turbo:frame-load",
        this.fetchLocationFromSessionStorageOnFirstLoad.bind(this),
      )
      return
    }

    const nextLocationValue = {
      adresse: sessionStorage.getItem("adresse"),
      latitude: sessionStorage.getItem("latitude"),
      longitude: sessionStorage.getItem("longitude"),
    }

    if (Object.values(nextLocationValue).find((value) => !!value)) {
      this.locationValue = nextLocationValue
    }
  }

  resetBboxInputs() {
    for (const outlet of this.searchSolutionFormOutlets) {
      outlet.resetBboxInput()
    }
  }

  setLocation(event) {
    this.resetBboxInputs()
    const nextLocationValue = event.detail
    const updatedLocationIsNotEmpty = !isEmpty(nextLocationValue)
    if (updatedLocationIsNotEmpty) {
      this.locationValue = nextLocationValue
    }
  }

  locationValueChanged(value, previousValue) {
    if (value && previousValue) {
      this.persistInSessionStorageIfChanged(value.adresse, "adresse")
      this.persistInSessionStorageIfChanged(value.latitude, "latitude")
      this.persistInSessionStorageIfChanged(value.longitude, "longitude")
    }

    for (const outlet of this.addressAutocompleteOutlets) {
      this.updateUIFromGlobalState(outlet)
    }
  }

  updateUIFromGlobalState(outlet) {
    const value = this.locationValue
    let touched = false
    if (value.adresse && value.adresse !== outlet.inputTarget.value) {
      outlet.inputTarget.value = value.adresse
      touched = true
    }

    if (value.latitude && outlet.latitudeTarget.value !== value.latitude) {
      outlet.latitudeTarget.value = value.latitude
      touched = true
    }

    if (value.longitude && outlet.longitudeTarget.value !== value.longitude) {
      outlet.longitudeTarget.value = value.longitude
      touched = true
    }

    if (touched) {
      this.submit()
    }
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
