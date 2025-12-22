import { Controller } from "@hotwired/stimulus"

export default class MapAddressAutocompleteController extends Controller {
  static targets = ["latitudeInput", "longitudeInput", "input"]

  declare readonly latitudeInputTarget: HTMLInputElement
  declare readonly longitudeInputTarget: HTMLInputElement
  declare readonly inputTarget: HTMLInputElement

  connect() {
    console.log("MapAddressAutocompleteController connected", this.element)
    // Listen for the custom event from next-autocomplete controller
    this.element.addEventListener(
      "next-autocomplete:commit",
      this.handleSelection.bind(this),
    )
  }

  disconnect() {
    this.element.removeEventListener(
      "next-autocomplete:commit",
      this.handleSelection.bind(this),
    )
  }

  handleSelection(event: CustomEvent) {
    const { option, value } = event.detail

    console.log("COUCOU", { option, value })
    if (!option) return

    const latitude = option.dataset.latitude
    const longitude = option.dataset.longitude

    if (latitude && longitude) {
      this.latitudeInputTarget.value = latitude
      this.longitudeInputTarget.value = longitude

      // Set the input value to the selected address
      if (this.hasInputTarget && value) {
        this.inputTarget.value = value
      }

      // Submit the form (matches address_autocomplete_controller behavior)
      this.dispatch("formSubmit")
    }
  }
}
