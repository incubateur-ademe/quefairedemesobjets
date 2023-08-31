import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    #allAvailableOptions: Array<string> = []
    #currentFocus: number = 0
    #autocompleteList: HTMLElement

    static targets = ["allAvailableOptions", "input", "option", "long", "lat"]
    declare readonly allAvailableOptionsTarget: HTMLScriptElement
    declare readonly inputTarget: HTMLInputElement
    declare readonly latTarget: HTMLInputElement
    declare readonly longTarget: HTMLInputElement
    declare readonly optionTargets: Array<HTMLElement>

    static values = { maxOptionDisplayed: Number, searchCallback: String }
    declare readonly searchCallbackValue: string
    declare readonly maxOptionDisplayedValue: number

    connect() {
        if (this.allAvailableOptionsTarget.textContent != null) {
            this.#allAvailableOptions = JSON.parse(
                this.allAvailableOptionsTarget.textContent,
            )
        }

        if (
            this.searchCallbackValue == "true" &&
            "geolocation" in navigator &&
            this.inputTarget.value == ""
        ) {
            if (this.inputTarget.value == "") {
                navigator.geolocation.getCurrentPosition((position) => {
                    fetch(
                        `https://api-adresse.data.gouv.fr/reverse/?lon=${position.coords.longitude}&lat=${position.coords.latitude}`,
                    )
                        .then((response) => response.json())
                        .then((data) => {
                            this.inputTarget.value = data.features[0].properties.label
                            this.latTarget.value =
                                data.features[0].geometry.coordinates[1]
                            this.longTarget.value =
                                data.features[0].geometry.coordinates[0]
                            /* FIXME : Check if we can partially refresh the page using Turbo */
                            this.inputTarget.form.submit()
                        })
                })
            }
        }
    }

    async complete(events: Event) {
        const inputTargetValue = this.inputTarget.value
        const val = this.#addAccents(inputTargetValue)
        const regexPattern = new RegExp(val, "gi")

        if (!val) {
            this.#closeAllLists()
            return false
        }

        let countResult = 0

        if (this.searchCallbackValue) {
            this.#searchAddressCallback(inputTargetValue).then((data) => {
                this.#closeAllLists()
                this.#autocompleteList = this.#createAutocompleteList()
                this.#allAvailableOptions = data
                for (let i = 0; i < this.#allAvailableOptions.length; i++) {
                    if (countResult >= this.maxOptionDisplayedValue) break
                    countResult++
                    this.#addoption(regexPattern, this.#allAvailableOptions[i])
                }
                if (this.#autocompleteList.childElementCount > 0) {
                    this.#currentFocus = 0
                    this.#addActive()
                }
            })
        } else {
            /*for each item in the array...*/
            this.#closeAllLists()
            this.#autocompleteList = this.#createAutocompleteList()

            for (let i = 0; i < this.#allAvailableOptions.length; i++) {
                if (countResult >= this.maxOptionDisplayedValue) break
                /*check if the item starts with the same letters as the text field value:*/
                if (this.#allAvailableOptions[i].match(regexPattern) !== null) {
                    countResult++
                    this.#addoption(regexPattern, this.#allAvailableOptions[i])
                }
                // FIXME : check if list is empty
                if (this.#autocompleteList.childElementCount > 0) {
                    this.#currentFocus = 0
                    this.#addActive()
                }
            }
        }
    }

    selectOption(event: Event) {
        let target = event.target as HTMLElement
        const [label, lat, long] = target
            .getElementsByTagName("input")[0]
            .value.split("||")
        this.inputTarget.value = label
        if (long) this.longTarget.value = long
        if (lat) this.latTarget.value = lat
        this.inputTarget.form.submit()
        this.#closeAllLists()
    }

    keydownDown(event: KeyboardEvent) {
        this.#currentFocus++
        this.#addActive()
    }

    keydownUp(event: KeyboardEvent) {
        this.#currentFocus--
        this.#addActive()
    }

    keydownEnter(event: KeyboardEvent) {
        var x = document.getElementById(this.inputTarget.id + "autocomplete-list")
        let optionDiv: HTMLCollectionOf<HTMLElement> | undefined
        if (x) {
            optionDiv = x.getElementsByTagName("div")
        }

        /*If the ENTER key is pressed, prevent the form from being submitted when select an option */
        if (optionDiv !== undefined && optionDiv?.length > 0) {
            event.preventDefault()
        }
        if (this.#currentFocus > -1) {
            /*and simulate a click on the "active" item:*/
            if (optionDiv) optionDiv[this.#currentFocus].click()
        }
    }

    #closeAllLists() {
        var x = document.getElementsByClassName("autocomplete-items")
        for (var i = 0; i < x.length; i++) {
            x[i].remove()
        }
    }

    #addActive() {
        var x: HTMLElement | null = document.getElementById(
            this.inputTarget.id + "autocomplete-list",
        )
        let optionDiv: HTMLCollectionOf<HTMLElement> | undefined
        if (x) {
            optionDiv = x.getElementsByTagName("div")
        }

        /*a function to classify an item as "active":*/
        if (!optionDiv) return false
        /*start by removing the "active" class on all items:*/
        this.#removeActive(optionDiv)
        if (this.#currentFocus >= optionDiv.length) this.#currentFocus = 0
        if (this.#currentFocus < 0) this.#currentFocus = optionDiv.length - 1
        /*add class "autocomplete-active":*/
        optionDiv[this.#currentFocus].classList.add("autocomplete-active")
    }

    #removeActive(optionDiv: HTMLCollectionOf<HTMLElement>) {
        for (var i = 0; i < optionDiv.length; i++) {
            optionDiv[i].classList.remove("autocomplete-active")
        }
    }

    #addAccents(input: string) {
        let retval = input
        retval = retval.replace(/([ao])e/gi, "$1")
        retval = retval.replace(/e/gi, "[eèéêë]")
        retval = retval.replace(/c/gi, "[cç]")
        retval = retval.replace(/i/gi, "[iîï]")
        retval = retval.replace(/u/gi, "[uùûü]")
        retval = retval.replace(/y/gi, "[yÿ]")
        retval = retval.replace(/s/gi, "(ss|[sß])")
        retval = retval.replace(/a/gi, "([aàâä]|ae)")
        retval = retval.replace(/o/gi, "([oôö]|oe)")
        return retval
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
                    ].join("||")
                })
                return labels
            })
            .catch((error) => {
                console.error("error catched : ", error)
                return []
            })
    }

    #addoption(regexPattern: RegExp, option: string) {
        //option : this.#allAvailableOptions[i]
        /*create a DIV element for each matching element:*/
        let b = document.createElement("DIV")
        /*make the matching letters bold:*/
        const [data, long, lat] = option.split("||")
        const newText = data.replace(regexPattern, "<strong>$&</strong>")
        b.innerHTML = newText
        // FIXME : better way to do this
        b.innerHTML += "<input type='hidden' value='" + option + "'>"
        b.setAttribute("data-action", "click->autocomplete#selectOption")
        this.#autocompleteList.appendChild(b)
    }

    #createAutocompleteList() {
        /*create a DIV element that will contain the items (values):*/
        let a = document.createElement("DIV")
        a.setAttribute("id", this.inputTarget.id + "autocomplete-list")
        a.setAttribute("class", "autocomplete-items")
        /*append the DIV element as a child of the autocomplete container:*/
        if (this.inputTarget.parentNode != null)
            this.inputTarget.parentNode.appendChild(a)
        return a
    }
}
