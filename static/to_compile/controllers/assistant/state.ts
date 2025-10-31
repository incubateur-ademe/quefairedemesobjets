import { Controller } from "@hotwired/stimulus"
import isEmpty from "lodash/isEmpty"
import AdresseAutocompleteController from "../carte/address_autocomplete_controller"
import SearchFormController from "../carte/search_solution_form_controller"

export default class extends Controller<HTMLElement> {
  static values = {
    location: Object,
    iframe: Boolean,
  }
  static outlets = ["address-autocomplete", "search-solution-form"]
  declare addressAutocompleteOutlets: Array<AdresseAutocompleteController>
  declare searchSolutionFormOutlets: Array<SearchFormController>
  declare locationValue: {
    adresse: string | null
    latitude: string | null
    longitude: string | null
  }
  declare iframeValue: boolean
  hasAddressAutocompleteOutletConnected = false
  hasSearchSolutionFormOutletConnected = false

  connect() {
    this.fetchLocationFromSessionStorageOnFirstLoad()
    this.configureIframeSpecificUI()
  }

  addressAutocompleteOutletConnected(outlet, element) {
    if (outlet.inputTarget.value) {
      return
    }
    this.updateUIFromGlobalState(outlet)
  }

  #redirectIfIframeMisconfigured() {
    /**
    In some situation, the sessionStorage read a true value for iframe whereas
    the url does not contain the iframe param.
    The cause is yet unclear, but as fallback we detect this situation and redirect
    the user dynamically to the correct location, with iframe in the querystring.
    */
    const url = new URL(window.location.href)
    const params = url.searchParams

    if (!params.has("iframe")) {
      params.set("iframe", "1")
      url.search = params.toString()
      window.location.href = url.toString()
    }
  }

  configureIframeSpecificUI() {
    if (sessionStorage.getItem("iframe") === "true") {
      this.iframeValue = true
      this.#redirectIfIframeMisconfigured()
    }

    if (this.iframeValue) {
      document.querySelectorAll<HTMLLinkElement>('a[href^="/"]').forEach((link) => {
        const url = new URL(link.href, window.location.origin)
        url.searchParams.set("iframe", "1")
        link.href = url.toString()
      })
      sessionStorage.setItem("iframe", "true")
    }
  }

  fetchLocationFromSessionStorageOnFirstLoad() {
    if (!isEmpty(this.locationValue)) {
      return
    }

    const nextLocationValue = {
      adresse: sessionStorage.getItem("adresse"),
      latitude: sessionStorage.getItem("latitude"),
      longitude: sessionStorage.getItem("longitude"),
    }

    this.#setLocationValue(nextLocationValue)
  }

  resetBboxInputs() {
    for (const outlet of this.searchSolutionFormOutlets) {
      outlet.resetBboxInput()
    }
  }

  setLocation(event) {
    this.resetBboxInputs()
    const nextLocationValue = event.detail
    this.#setLocationValue(nextLocationValue)
  }

  #setLocationValue(nextLocationValue) {
    const updatedLocationIsNotEmpty = !isEmpty(nextLocationValue)
    if (updatedLocationIsNotEmpty) {
      this.locationValue = nextLocationValue

      for (const outlet of this.addressAutocompleteOutlets) {
        this.updateUIFromGlobalState(outlet)
      }
    }
  }

  locationValueChanged(value, previousValue) {
    // Persist UI changes in session storage
    this.persistInSessionStorageIfChanged(value?.adresse, "adresse")
    this.persistInSessionStorageIfChanged(value?.latitude, "latitude")
    this.persistInSessionStorageIfChanged(value?.longitude, "longitude")
  }

  updateUIFromGlobalState(outlet) {
    // Update a single Carte instance UI reading the state
    // stored globally in the page
    const value = this.locationValue
    let touched = false
    if (value.adresse) {
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
    // Submit all instances of Carte on the same page
    for (const outlet of this.searchSolutionFormOutlets) {
      outlet.submitForm()
    }
  }

  updateBbox(event) {
    // Update all bbox instances of Carte on the same page
    for (const outlet of this.searchSolutionFormOutlets) {
      outlet.updateBboxInput(event)
    }
  }

  persistInSessionStorageIfChanged(value, key) {
    if (!value) {
      return
    }

    if (value !== sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, value)
    }
  }
}
