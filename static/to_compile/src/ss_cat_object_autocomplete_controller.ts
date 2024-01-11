import AutocompleteController from "../src/autocomplete_controller"
import posthog from "./analytics"
import { SSCatObject } from "./types"

export default class extends AutocompleteController {
    controllerName: string = "ss-cat-object-autocomplete"
    allAvailableOptions: Array<SSCatObject> = []

    static targets = AutocompleteController.targets.concat(["ssCat"])
    declare readonly ssCatTarget: HTMLInputElement

    async search_to_complete(events: Event): Promise<void> {
        const inputTargetValue = this.inputTarget.value
        const val = this.addAccents(inputTargetValue)
        const regexPattern = new RegExp(val, "gi")

        if (!val) this.closeAllLists()

        let countResult = 0

        return this.#getOptionCallback(inputTargetValue)
            .then((data) => {
                this.closeAllLists()
                this.allAvailableOptions = data
                if (this.allAvailableOptions.length == 0) return

                this.autocompleteList = this.createAutocompleteList()
                for (let i = 0; i < this.allAvailableOptions.length; i++) {
                    if (countResult >= this.maxOptionDisplayedValue) break
                    countResult++
                    this.addOption(regexPattern, this.allAvailableOptions[i])
                }
                if (this.autocompleteList.childElementCount > 0) {
                    this.currentFocus = 0
                    this.addActive()
                }

                posthog.capture("sous_categorie_objet_research", {
                    object_requested: inputTargetValue,
                    object_list: this.allAvailableOptions,
                    main_object: this.allAvailableOptions
                        ? this.allAvailableOptions[0]["label"]
                        : undefined,
                    main_sous_categorie: this.allAvailableOptions
                        ? this.allAvailableOptions[0]["sub_label"]
                        : undefined,
                })
            })
            .then(() => {
                this.spinnerTarget.classList.add("qfdmo-hidden")
                return
            })
    }

    selectOption(event: Event) {
        const inputTargetValue = this.inputTarget.value

        let target = event.target as HTMLElement
        while (target && target.nodeName !== "DIV") {
            target = target.parentNode as HTMLElement
        }

        const labelElement = target.querySelector(
            '[data-type-name="label"]',
        ) as HTMLInputElement
        const labelValue = labelElement ? labelElement.value : ""
        this.inputTarget.value = labelValue

        const subLabelElement = target.querySelector(
            '[data-type-name="subLabel"]',
        ) as HTMLInputElement
        const subLabelValue = subLabelElement ? subLabelElement.value : ""

        const identifierElement = target.querySelector(
            '[data-type-name="identifier"]',
        ) as HTMLInputElement
        const identifierValue = identifierElement ? identifierElement.value : ""
        this.ssCatTarget.value = identifierValue

        posthog.capture("sous_categorie_objet_select", {
            object_requested: inputTargetValue,
            object_list: this.allAvailableOptions,
            object_selected: labelValue,
            sous_categorie_selected: subLabelValue,
            identifier_selected: identifierValue,
        })

        this.closeAllLists()
    }

    addOption(regexPattern: RegExp, option: SSCatObject) {
        //option : this.#allAvailableOptions[i]
        /*create a DIV element for each matching element:*/
        let b = document.createElement("DIV")
        b.classList.add(
            "qfdmo-flex",
            "qfdmo-flex-col",
            "md:qfdmo-flex-row",
            "md:qfdmo-justify-between",
        )
        /*make the matching letters bold:*/
        // const [data, longitude, latitude] = option.split("||")

        let label = document.createElement("span")
        const data = option.label
        const newText = data.replace(regexPattern, "<strong>$&</strong>")
        label.innerHTML = newText
        b.appendChild(label)

        if (option.sub_label != null) {
            const sub_label = document.createElement("span")
            sub_label.classList.add("fr-text--sm", "fr-m-0", "qfdmo-italic")
            sub_label.innerHTML = option.sub_label
            b.appendChild(sub_label)
        }

        // Input hidden
        const labelInput = document.createElement("input")
        labelInput.setAttribute("type", "hidden")
        labelInput.setAttribute("data-type-name", "label")
        labelInput.setAttribute("value", option.label)
        b.appendChild(labelInput)
        const identifierInput = document.createElement("input")
        identifierInput.setAttribute("type", "hidden")
        identifierInput.setAttribute("data-type-name", "identifier")
        identifierInput.setAttribute("value", option.identifier)
        b.appendChild(identifierInput)
        const input = document.createElement("input")
        input.setAttribute("type", "hidden")
        input.setAttribute("data-type-name", "subLabel")
        input.setAttribute("value", option.sub_label ? option.sub_label : "")
        b.appendChild(input)
        b.setAttribute("data-action", "click->" + this.controllerName + "#selectOption")
        b.setAttribute("data-on-focus", "true")
        this.autocompleteList.appendChild(b)
    }

    async #getOptionCallback(value: string): Promise<SSCatObject[]> {
        if (value.trim().length < this.nbCharToSearchValue) return []
        return await fetch(`/qfdmo/get_object_list?q=${value}`)
            .then((response) => response.json())
            .then((data) => {
                return data
            })
            .catch((error) => {
                console.error("error catched : ", error)
                return []
            })
    }
}
