import { Controller } from "@hotwired/stimulus"
import isEmpty from "lodash/isEmpty"
import AdresseAutocompleteController from "../carte/address_autocomplete_controller"
import CarteAddressAutocompleteController from "../carte/carte_address_autocomplete_controller"
import SearchFormController from "../carte/search_solution_form_controller"

// Both address autocomplete controllers expose the same target contract for
// the state controller's purposes: an `input` for the visible address,
// `latitude` and `longitude` for the hidden coordinate fields.
type AddressOutlet = AdresseAutocompleteController | CarteAddressAutocompleteController

// Exempt from consent (validated with Numéricité) as long as it expires.
const LOCATION_MAX_AGE_IN_DAYS = 30
const LOCATION_KEYS = ["adresse", "latitude", "longitude"] as const
const LOCATION_SAVED_AT_KEY = "adresse_enregistree_le"

function readStoredLocation() {
  const savedAt = Number(localStorage.getItem(LOCATION_SAVED_AT_KEY))
  if (Date.now() - savedAt > LOCATION_MAX_AGE_IN_DAYS * 24 * 60 * 60 * 1000) {
    for (const key of [...LOCATION_KEYS, LOCATION_SAVED_AT_KEY]) {
      localStorage.removeItem(key)
    }
  }
  return {
    adresse: localStorage.getItem("adresse"),
    latitude: localStorage.getItem("latitude"),
    longitude: localStorage.getItem("longitude"),
  }
}

export default class extends Controller<HTMLElement> {
  static values = {
    location: Object,
  }
  static outlets = [
    "address-autocomplete",
    "carte-address-autocomplete",
    "search-solution-form",
  ]
  declare addressAutocompleteOutlets: Array<AdresseAutocompleteController>
  declare carteAddressAutocompleteOutlets: Array<CarteAddressAutocompleteController>
  declare searchSolutionFormOutlets: Array<SearchFormController>
  declare locationValue: {
    adresse: string | null
    latitude: string | null
    longitude: string | null
  }
  hasAddressAutocompleteOutletConnected = false
  hasSearchSolutionFormOutletConnected = false

  connect() {
    this.fetchStoredLocationOnFirstLoad()
  }

  addressAutocompleteOutletConnected(outlet, element) {
    if (outlet.inputTarget.value) {
      return
    }
    this.updateUIFromGlobalState(outlet)
  }

  carteAddressAutocompleteOutletConnected(outlet) {
    if (outlet.inputTarget.value) {
      return
    }
    this.updateUIFromGlobalState(outlet)
  }

  fetchStoredLocationOnFirstLoad() {
    if (!isEmpty(this.locationValue)) {
      return
    }

    this.#setLocationValue(readStoredLocation())
  }

  resetBboxInputs() {
    for (const outlet of this.searchSolutionFormOutlets) {
      outlet.resetBboxInput()
    }
  }

  setLocation(event) {
    // The user explicitly picked a new address. Drop any stale bbox that the
    // map controller left behind from a previous pan — otherwise the form
    // submit below would still scope acteurs to the old map view.
    this.resetBboxInputs()
    const nextLocationValue = event.detail
    this.#setLocationValue(nextLocationValue)
    // The carte controller already wrote the new lat/lon onto its targets
    // before dispatching `change`, so #setLocationValue → updateUIFromGlobalState
    // sees the DOM in sync and won't submit on its own. Submit explicitly here
    // so the form re-fetches acteurs around the new address.
    this.submit()
  }

  #setLocationValue(nextLocationValue) {
    const updatedLocationIsNotEmpty = !isEmpty(nextLocationValue)
    if (updatedLocationIsNotEmpty) {
      this.locationValue = nextLocationValue

      const allOutlets: Array<AddressOutlet> = [
        ...this.addressAutocompleteOutlets,
        ...this.carteAddressAutocompleteOutlets,
      ]
      for (const outlet of allOutlets) {
        this.updateUIFromGlobalState(outlet)
      }
    }
  }

  locationValueChanged(value) {
    let changed = false
    for (const key of LOCATION_KEYS) {
      if (value?.[key] && value[key] !== localStorage.getItem(key)) {
        localStorage.setItem(key, value[key])
        changed = true
      }
    }
    if (changed) {
      localStorage.setItem(LOCATION_SAVED_AT_KEY, String(Date.now()))
    }
  }

  updateUIFromGlobalState(outlet) {
    // Update a single Carte instance UI reading the state
    // stored globally in the page
    const value = this.locationValue
    let touched = false
    if (value.adresse && outlet.inputTarget.value !== value.adresse) {
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
}
