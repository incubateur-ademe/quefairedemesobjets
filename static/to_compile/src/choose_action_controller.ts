import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    #selectedOption: string = "jecherche"
    static targets = [
        "jai",
        "jecherche",
        "direction",
        "apply",
        "actionList",
        "advancedFilters",
        "advancedField",
        "advancedFieldsCounter",
    ]
    declare readonly jaiTarget: HTMLElement
    declare readonly jechercheTarget: HTMLElement
    declare readonly directionTarget: HTMLElement
    declare readonly applyTarget: HTMLElement
    declare readonly actionListTarget: HTMLInputElement
    declare readonly advancedFiltersTarget: HTMLElement
    declare readonly advancedFieldTargets: HTMLInputElement[]
    declare readonly advancedFieldsCounterTarget: HTMLElement

    connect() {
        this.displayActionList()
        this.updateAdvancedFiltersCounter()
    }

    displayActionList() {
        const direction = this.directionTarget
        const options = direction.getElementsByTagName("input")
        for (let i = 0; i < options.length; i++) {
            if (options[i].checked && options[i].value == "jai") {
                this.#selectedOption = "jai"
                this.jechercheTarget.hidden = true
                this.jaiTarget.hidden = false
            }
            if (options[i].checked && options[i].value == "jecherche") {
                this.#selectedOption = "jecherche"
                this.jechercheTarget.hidden = false
                this.jaiTarget.hidden = true
            }
        }
    }

    apply() {
        const direction = this.directionTarget
        const options = direction.getElementsByTagName("input")
        for (let i = 0; i < options.length; i++) {
            if (options[i].value == this.#selectedOption) options[i].checked = true
            else options[i].checked = false
        }

        let actionList = []
        if (this.#selectedOption == "jai") {
            // Checkboxes option
            const actionInput = this.jaiTarget.getElementsByTagName("input")
            for (let i = 0; i < actionInput.length; i++) {
                if (actionInput[i].checked)
                    actionList.push(actionInput[i].getAttribute("name"))
            }
        }
        if (this.#selectedOption == "jecherche") {
            // Checkboxes option
            const actionInput = this.jechercheTarget.getElementsByTagName("input")
            for (let i = 0; i < actionInput.length; i++) {
                if (actionInput[i].checked)
                    actionList.push(actionInput[i].getAttribute("name"))
            }
        }
        this.actionListTarget.value = actionList.join("|")
    }

    changeDirection() {
        this.actionListTarget.value = ""
        this.displayActionList()
        this.apply()
    }

    toggleAdvancedFilters() {
        this.advancedFiltersTarget.classList.toggle("qfdmo-hidden")
        const advancedFields = this.advancedFieldTargets
        for (let i = 0; i < advancedFields.length; i++) {
            console.log(advancedFields[i].value)
        }
    }

    updateAdvancedFiltersCounter() {
        const advancedFields = this.advancedFieldTargets
        let counter = 0
        for (let i = 0; i < advancedFields.length; i++) {
            if (advancedFields[i].checked) counter++
        }
        if (counter == 0) {
            this.advancedFieldsCounterTarget.innerText = ""
            this.advancedFieldsCounterTarget.classList.add("qfdmo-hidden")
            return
        }
        this.advancedFieldsCounterTarget.innerText = counter.toString()
        this.advancedFieldsCounterTarget.classList.remove("qfdmo-hidden")
    }
}
