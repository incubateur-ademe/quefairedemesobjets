import AutocompleteController from "./autocomplete_controller"

class AdresseAutocompleteController extends AutocompleteController {
  controllerName: string = "address-autocomplete"

  static targets = AutocompleteController.targets.concat([
    "longitude",
    "latitude",
    "displayError",
  ])

  declare readonly latitudeTarget: HTMLInputElement
  declare readonly longitudeTarget: HTMLInputElement
  declare readonly displayErrorTarget: HTMLElement

  async searchToComplete(events: Event): Promise<void> {
    const inputTargetValue = this.inputTarget.value
    const val = this.addAccents(inputTargetValue)
    const regexPattern = new RegExp(val, "gi")

    if (!val) this.hideAutocompleteList()

    let countResult = 0

    const data = await this.#getOptionCallback(inputTargetValue)
    this.hideAutocompleteList()
    this.autocompleteList = this.createAutocompleteList()
    this.allAvailableOptions = data
    for (let i = 0; i < data.length; i++) {
      if (countResult >= this.maxOptionDisplayedValue + 1) break
      countResult++
      this.addOption(regexPattern, data[i])
    }
    if (this.autocompleteList.childElementCount > 0) {
      this.currentFocusedOptionIndexValue = 0
    }
    this.hideSpinner()
  }

  async selectOption(event: Event) {
    let target = event.target as HTMLElement

    while (target && target.nodeName !== "DIV") {
      target = target.parentNode as HTMLElement
    }

    const option = JSON.parse(target.getElementsByTagName("input")[0].value)
    const labelValue = option.label
    const longitudeValue = option.longitude
    const latitudeValue = option.latitude

    // TODO: Explain where do these values come from
    if (
      longitudeValue == "9999" &&
      latitudeValue == "9999" &&
      "geolocation" in navigator
    ) {
      this.displaySpinner()
      navigator.geolocation.getCurrentPosition(
        this.getAndStorePosition.bind(this),
        () => this.geolocationRefused(),
      )
    } else if (!("geolocation" in navigator)) {
      console.error("geolocation is not available")
    } else {
      this.dispatchLocationToGlobalState(labelValue, latitudeValue, longitudeValue)
    }
    this.hideAutocompleteList()
  }

  async getAndStorePosition(position: GeolocationPosition) {
    try {
      const response = await fetch(
        `https://data.geopf.fr/geocodage/reverse/?lon=${position.coords.longitude}&lat=${position.coords.latitude}`,
      )
      const data = await response.json()
      if (data.features.length == 0) {
        this.geolocationRefused(
          "Votre adresse n'a pas pu être déterminée. Vous pouvez ré-essayer ou saisir votre adresse manuellement",
        )
        return
      }

      this.dispatchLocationToGlobalState(
        data.features[0].properties.label,
        data.features[0].geometry.coordinates[1],
        data.features[0].geometry.coordinates[0],
      )

      this.#hideInputError()
      this.hideSpinner()
    } catch (error) {
      console.error("error catched : ", error)
      this.hideSpinner()
    }
  }

  dispatchLocationToGlobalState(adresse: string, latitude: string, longitude: string) {
    this.dispatch("locationUpdated", { detail: { adresse, latitude, longitude } })
  }

  keydownEnter(event: KeyboardEvent): boolean {
    let toSubmit = super.keydownEnter(event)
    if (toSubmit) {
      this.dispatch("formSubmit")
    }
    return toSubmit
  }

  geolocationRefused(message?: string) {
    message = message || "La géolocalisation est inaccessible sur votre appareil"
    this.#displayInputError(message)
    this.inputTarget.value = ""
    this.longitudeTarget.value = ""
    this.latitudeTarget.value = ""
    this.hideSpinner()
  }

  #displayInputError(errorText: string): void {
    this.inputTarget.classList.add("fr-input--error")
    this.inputTarget.parentElement.classList.add("fr-input-group--error")
    this.displayErrorTarget.innerHTML = errorText
    this.displayErrorTarget.style.display = "block"
  }

  #hideInputError() {
    this.inputTarget.classList.remove("fr-input--error")
    this.inputTarget.parentElement.classList.remove("fr-input-group--error")
    this.displayErrorTarget.style.display = "none"
  }

  async #getOptionCallback(value: string): Promise<object[]> {
    if (value.trim().length < 3) {
      this.latitudeTarget.value = this.longitudeTarget.value = ""
      return [{ label: "Autour de moi", longitude: 9999, latitude: 9999 }]
    }
    return await fetch(`https://data.geopf.fr/geocodage/search/?q=${value}`)
      .then((response) => response.json())
      .then((data) => {
        let labels = data.features
          .slice(0, this.maxOptionDisplayedValue)
          .map((feature: any) => {
            return {
              label: feature.properties.label,
              sub_label: feature.properties.context,
              longitude: feature.geometry.coordinates[0],
              latitude: feature.geometry.coordinates[1],
            }
          })
          .concat([{ label: "Autour de moi", longitude: 9999, latitude: 9999 }])
        return labels
      })
      .catch((error) => {
        console.error("error catched : ", error)
        return []
      })
  }
}

export default AdresseAutocompleteController
