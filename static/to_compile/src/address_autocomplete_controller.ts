import AutocompleteController from "./autocomplete_controller"

const SEPARATOR = "||"
export default class extends AutocompleteController {
    controllerName: string = "address-autocomplete"
    allAvailableOptions: Array<string> = []

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

        return this.#getOptionCallback(inputTargetValue)
            .then((data) => {
                this.hideAutocompleteList()
                this.autocompleteList = this.createAutocompleteList()
                this.allAvailableOptions = data
                for (let i = 0; i < this.allAvailableOptions.length; i++) {
                    if (countResult >= this.maxOptionDisplayedValue) break
                    countResult++
                    this.addOption(regexPattern, this.allAvailableOptions[i])
                }
                if (this.autocompleteList.childElementCount > 0) {
                    this.currentFocusedOptionIndexValue = 0
                }
                return
            })
            .then(() => {
                this.spinnerTarget.classList.add("qf-hidden")
                return
            })
    }

    selectOption(event: Event) {
        let target = event.target as HTMLElement
        while (target && target.nodeName !== "DIV") {
            target = target.parentNode as HTMLElement
        }
        const [label, latitude, longitude] = target
            .getElementsByTagName("input")[0]
            .value.split(SEPARATOR)
        if (longitude == "9999" && latitude == "9999") {
            if ("geolocation" in navigator) {
                this.displaySpinner()
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        fetch(
                            `https://api-adresse.data.gouv.fr/reverse/?lon=${position.coords.longitude}&lat=${position.coords.latitude}`,
                        )
                            .then((response) => response.json())
                            .then((data) => {
                                if (data.features.length == 0) {
                                    this.geolocatisationRefused(
                                        "Votre adresse n'a pas pu être déterminée. Vous pouvez ré-essayer ou saisir votre adresse manuellement",
                                    )
                                    return
                                }
                                this.inputTarget.value =
                                    data.features[0].properties.label
                                this.latitudeTarget.value =
                                    data.features[0].geometry.coordinates[1]
                                this.longitudeTarget.value =
                                    data.features[0].geometry.coordinates[0]
                                this.#hideInputError()
                                this.hideSpinner()
                            })
                            .then(() => {
                                this.dispatch("optionSelected")
                            })
                            .catch((error) => {
                                console.error("error catched : ", error)
                                this.hideSpinner()
                            })
                    },
                    () => this.geolocatisationRefused(),
                )
            } else {
                console.error("geolocation is not available")
            }
        } else {
            this.inputTarget.value = label
            if (longitude) this.longitudeTarget.value = longitude
            if (latitude) this.latitudeTarget.value = latitude
            this.dispatch("optionSelected")
        }
        this.hideAutocompleteList()
    }

    addOption(regexPattern: RegExp, option: any) {
        //option : this.#allAvailableOptions[i]
        /*create a DIV element for each matching element:*/
        let b = document.createElement("DIV")
        /*make the matching letters bold:*/
        const [data, longitude, latitude] = option.split("||")
        const newText = data.replace(regexPattern, "<strong>$&</strong>")
        b.innerHTML = newText
        // FIXME : better way to do this
        const input = document.createElement("input")
        input.setAttribute("type", "hidden")
        input.setAttribute("value", option)
        b.appendChild(input)
        b.setAttribute("data-action", "click->" + this.controllerName + "#selectOption")
        b.setAttribute("data-on-focus", "true")
        this.autocompleteList.appendChild(b)
    }

    keydownEnter(event: KeyboardEvent): boolean {
        let toSubmit = super.keydownEnter(event)
        if (toSubmit) {
            this.dispatch("formSubmit")
        }
        return toSubmit
    }

    geolocatisationRefused(message?: string) {
        message = message || "La géolocalisation est inaccessible sur votre appareil"
        this.#displayInputError(message)
        this.inputTarget.value = ""
        this.longitudeTarget.value = ""
        this.latitudeTarget.value = ""
        this.hideSpinner()
    }

    #displayInputError(errorText: string): void {
        console.error(errorText)
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

    async #getOptionCallback(value: string): Promise<string[]> {
        if (value.trim().length < 3) {
            this.latitudeTarget.value = this.longitudeTarget.value = ""
            return [["Autour de moi", 9999, 9999].join(SEPARATOR)]
        }
        return await fetch(`https://api-adresse.data.gouv.fr/search/?q=${value}`)
            .then((response) => response.json())
            .then((data) => {
                let labels = [["Autour de moi", 9999, 9999].join(SEPARATOR)].concat(
                    data.features.map((feature: any) => {
                        return [
                            feature.properties.label,
                            feature.geometry.coordinates[1],
                            feature.geometry.coordinates[0],
                        ].join(SEPARATOR)
                    }),
                )
                return labels
            })
            .catch((error) => {
                console.error("error catched : ", error)
                return []
            })
    }
}
