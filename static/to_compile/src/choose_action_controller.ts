import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    #selectedOption: string = "jecherche"
    static targets = [
        "jai",
        "jecherche",
        "direction",
        "apply",
        "actionList",
        "sideoverContainer",
        "digital",
    ]
    declare readonly jaiTarget: HTMLElement
    declare readonly jechercheTarget: HTMLElement
    declare readonly directionTarget: HTMLElement
    declare readonly applyTarget: HTMLElement
    declare readonly actionListTarget: HTMLInputElement
    declare readonly sideoverContainerTarget: HTMLDivElement
    declare readonly digitalTarget: HTMLInputElement

    connect() {
        this.displayActionList()
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
            // Buttons option
            const actionButtons = this.jaiTarget.getElementsByTagName("button")
            for (let i = 0; i < actionButtons.length; i++) {
                if (actionButtons[i].getAttribute("aria-pressed") == "true")
                    actionList.push(actionButtons[i].getAttribute("name"))
            }
            // Checkboxes option
            const actionInput = this.jaiTarget.getElementsByTagName("input")
            for (let i = 0; i < actionInput.length; i++) {
                if (actionInput[i].checked)
                    actionList.push(actionInput[i].getAttribute("name"))
            }
        }
        if (this.#selectedOption == "jecherche") {
            // Buttons option
            const actionButtons = this.jechercheTarget.getElementsByTagName("button")
            for (let i = 0; i < actionButtons.length; i++) {
                if (actionButtons[i].getAttribute("aria-pressed") == "true")
                    actionList.push(actionButtons[i].getAttribute("name"))
            }
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

    toggleSideover() {
        this.sideoverContainerTarget.classList.toggle("qfdmo-invisible")
        this.digitalTarget.value = this.digitalTarget.value ? "" : "1"
    }
}
