import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    #selectedOption: string = "jecherche"
    static targets = [
        "jai",
        "jecherche",
        "direction",
        "actionList",
        "advancedFiltersDiv",
        "advancedFiltersField",
        "advancedFiltersCounter",
        "action",
        "advancedFiltersButton",
        "nearbyButton",
        "onlineButton",
        "submitButton",
    ]
    declare readonly jaiTarget: HTMLElement
    declare readonly jechercheTarget: HTMLElement
    declare readonly directionTarget: HTMLElement
    declare readonly actionListTarget: HTMLInputElement
    declare readonly advancedFiltersDivTarget: HTMLElement
    declare readonly advancedFiltersFieldTargets: HTMLInputElement[]
    declare readonly actionTargets: HTMLInputElement[]
    declare readonly advancedFiltersCounterTarget: HTMLElement
    declare readonly advancedFiltersButtonTarget: HTMLElement
    declare readonly nearbyButtonTarget: HTMLButtonElement
    declare readonly onlineButtonTarget: HTMLButtonElement
    declare readonly submitButtonTarget: HTMLButtonElement

    connect() {
        this.displayActionList()
        this.updateAdvancedFiltersCounter()
        this.updateSearchSolutionForm()
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
        this.updateSearchSolutionForm()
    }

    toggleadvancedFiltersDiv() {
        this.advancedFiltersDivTarget.classList.toggle("qfdmo-hidden")
    }

    updateAdvancedFiltersCounter() {
        const advancedFiltersFields = this.advancedFiltersFieldTargets
        let counter = 0
        for (let i = 0; i < advancedFiltersFields.length; i++) {
            if (advancedFiltersFields[i].checked) counter++
        }
        if (counter == 0) {
            this.advancedFiltersCounterTarget.innerText = ""
            this.advancedFiltersCounterTarget.classList.add("qfdmo-hidden")
            return
        }
        this.advancedFiltersCounterTarget.innerText = counter.toString()
        this.advancedFiltersCounterTarget.classList.remove("qfdmo-hidden")
    }

    updateSearchSolutionForm() {
        const reparer = this.actionTargets.find(
            (element) => element.id == "jai_reparer",
        )
        if (this.#selectedOption == "jai" && reparer.checked) {
            this.advancedFiltersButtonTarget.classList.remove("qfdmo-hidden")
        } else {
            this.advancedFiltersButtonTarget.classList.add("qfdmo-hidden")
            this.advancedFiltersDivTarget.classList.add("qfdmo-hidden")
        }
    }

    toggleSolutionButtonView(event: Event) {
        let target = event.target as HTMLElement
        while (target && target.nodeName !== "BUTTON") {
            target = target.parentNode as HTMLElement
        }

        if (target == this.nearbyButtonTarget) {
            this.nearbyButtonTarget.classList.add("qfdmo-bg-white")
            this.onlineButtonTarget.classList.remove("qfdmo-bg-white")
            this.submitButtonTarget.value = "0"
        }
        if (target == this.onlineButtonTarget) {
            this.onlineButtonTarget.classList.add("qfdmo-bg-white")
            this.nearbyButtonTarget.classList.remove("qfdmo-bg-white")
            this.submitButtonTarget.value = "1"
        }
        this.loadingSolutions()
    }

    loadingSolutions() {
        this.dispatch("loadingSolutions", { detail: {} })
    }
}
