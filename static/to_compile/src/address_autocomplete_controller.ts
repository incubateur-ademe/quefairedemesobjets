import AutocompleteController from "../src/autocomplete_controller"
const debounce = require("lodash/debounce")

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

    initialize() {
        // display spinner
        this.complete = debounce(this.complete, 300).bind(this)
    }

    async complete(events: Event): Promise<boolean> {
        const inputTargetValue = this.inputTarget.value
        const val = this.addAccents(inputTargetValue)
        const regexPattern = new RegExp(val, "gi")

        if (!val) {
            this.closeAllLists()
        }

        let countResult = 0

        this.#getOptionCallback(inputTargetValue).then((data) => {
            this.closeAllLists()
            this.autocompleteList = this.createAutocompleteList()
            this.allAvailableOptions = data
            for (let i = 0; i < this.allAvailableOptions.length; i++) {
                if (countResult >= this.maxOptionDisplayedValue) break
                countResult++
                this.addOption(regexPattern, this.allAvailableOptions[i])
            }
            if (this.autocompleteList.childElementCount > 0) {
                this.currentFocus = 0
                this.addActive()
            }
        })
        return true
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
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        fetch(
                            `https://api-adresse.data.gouv.fr/reverse/?lon=${position.coords.longitude}&lat=${position.coords.latitude}`,
                        )
                            .then((response) => response.json())
                            .then((data) => {
                                this.inputTarget.value =
                                    data.features[0].properties.label
                                this.latitudeTarget.value =
                                    data.features[0].geometry.coordinates[1]
                                this.longitudeTarget.value =
                                    data.features[0].geometry.coordinates[0]
                                this.#hideInputError()
                            })
                            .catch((error) => {
                                console.error("error catched : ", error)
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
        }
        this.closeAllLists()
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

    geolocatisationRefused() {
        this.#displayInputError(
            "La géolocalisation est inaccessible sur votre appareil",
        )
        this.inputTarget.value = ""
        this.longitudeTarget.value = ""
        this.latitudeTarget.value = ""
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
        if (value.trim().length < 3)
            return [["Autour de moi", 9999, 9999].join(SEPARATOR)]
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
