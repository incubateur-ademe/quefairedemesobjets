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
        (err) => this.geolocationRefused(err),
      )
    } else if (!("geolocation" in navigator)) {
      console.error("geolocation is not available")
    } else {
      // Resolve the commune polygon (when applicable) BEFORE dispatching the
      // location change. The bbox derived from the polygon is what makes the
      // form submit fit the area precisely; the polygon itself is pinned to
      // the searched citycode so the next page render can re-fetch it.
      const citycode = option.citycode as string | undefined
      const isMunicipality = option.type === "municipality"
      const cityCitycode = isMunicipality && citycode ? citycode : ""
      if (cityCitycode) {
        this.#applyCityArea(cityCitycode)
      } else {
        this.#clearCityArea()
      }
      this.dispatchLocationToGlobalState(
        labelValue,
        latitudeValue,
        longitudeValue,
        cityCitycode,
      )
    }
    this.hideAutocompleteList()
  }

  // Persist the citycode in the form's hidden field so it survives the Turbo
  // Frame submit. The post-swap MapController fetches the polygon from the
  // server (which has the bbox cached) and draws the outline. We deliberately
  // do not fetch the polygon here: it would be a wasted round-trip — the
  // bbox is already computed server-side at template-render time and the
  // outline only needs to be drawn once, after the Turbo swap.
  #applyCityArea(citycode: string): void {
    this.#setHiddenField("search_area_citycode", citycode)
    this.dispatch("area", { detail: { citycode } })
  }

  #clearCityArea(): void {
    this.#setHiddenField("search_area_citycode", "")
    this.dispatch("area", { detail: { citycode: "", bbox: null, polygon: null } })
  }

  // Find a hidden input by suffix-name within the same form (the form name is
  // prefix-namespaced, e.g. `carte_map-search_area_citycode`).
  #setHiddenField(suffix: string, value: string): void {
    const form = this.element.closest("form")
    if (!form) return
    const input = form.querySelector<HTMLInputElement>(
      `input[name$="-${suffix}"], input[name="${suffix}"]`,
    )
    if (input) input.value = value
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

      // Mirror selectOption's citycode gating: only persist a citycode for
      // municipality-typed BAN results, so the polygon outline only redraws
      // when the user actually picked a city (not a street/housenumber).
      const props = data.features[0].properties
      const cityCitycode =
        props.type === "municipality" && props.citycode ? props.citycode : ""
      if (cityCitycode) {
        this.#applyCityArea(cityCitycode)
      } else {
        this.#clearCityArea()
      }
      this.dispatchLocationToGlobalState(
        props.label,
        data.features[0].geometry.coordinates[1],
        data.features[0].geometry.coordinates[0],
        cityCitycode,
      )

      this.#hideInputError()
      this.hideSpinner()
    } catch (error) {
      console.error("error catched : ", error)
      this.hideSpinner()
    }
  }

  dispatchLocationToGlobalState(
    adresse: string,
    latitude: string,
    longitude: string,
    citycode: string = "",
  ) {
    this.dispatch("change", { detail: { adresse, latitude, longitude, citycode } })
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
              // The BAN feature type ("municipality" | "street" | "housenumber"
              // | "locality" | "town"). Used to decide whether to fetch a
              // commune polygon outline.
              type: feature.properties.type,
              // INSEE citycode (e.g. "56007"). Present on every BAN feature
              // and used to resolve a commune polygon.
              citycode: feature.properties.citycode,
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
