import AutocompleteController from "../src/autocomplete_controller"

const SEPARATOR = "||"
export default class extends AutocompleteController {
    controllerName: string = "address-autocomplete"

    static targets = AutocompleteController.targets.concat(["longitude", "latitude"])
    declare readonly latitudeTarget: HTMLInputElement
    declare readonly longitudeTarget: HTMLInputElement

    connect() {
        if (this.allAvailableOptionsTarget.textContent != null) {
            this.allAvailableOptions = JSON.parse(
                this.allAvailableOptionsTarget.textContent,
            )
        }
    }

    async complete(events: Event) {
        const inputTargetValue = this.inputTarget.value
        const val = this.addAccents(inputTargetValue)
        const regexPattern = new RegExp(val, "gi")

        if (!val) {
            this.closeAllLists()
            return false
        }

        let countResult = 0

        this.#searchAddressCallback(inputTargetValue).then((data) => {
            this.closeAllLists()
            this.autocompleteList = this.createAutocompleteList()
            this.allAvailableOptions = data
            for (let i = 0; i < this.allAvailableOptions.length; i++) {
                if (countResult >= this.maxOptionDisplayedValue) break
                countResult++
                this.addoption(regexPattern, this.allAvailableOptions[i])
            }
            if (this.autocompleteList.childElementCount > 0) {
                this.currentFocus = 0
                this.addActive()
            }
        })
    }

    selectOption(event: Event) {
        let target = event.target as HTMLElement
        const [label, latitude, longitude] = target
            .getElementsByTagName("input")[0]
            .value.split(SEPARATOR)
        this.inputTarget.value = label
        if (longitude) this.longitudeTarget.value = longitude
        if (latitude) this.latitudeTarget.value = latitude
        this.closeAllLists()
    }

    async #searchAddressCallback(value: string): Promise<string[]> {
        if (value.trim().length < 3) return []
        return await fetch(`https://api-adresse.data.gouv.fr/search/?q=${value}`)
            .then((response) => response.json())
            .then((data) => {
                let labels = data.features.map((feature: any) => {
                    return [
                        feature.properties.label,
                        feature.geometry.coordinates[1],
                        feature.geometry.coordinates[0],
                    ].join(SEPARATOR)
                })
                return labels
            })
            .catch((error) => {
                console.error("error catched : ", error)
                return []
            })
    }
}
