import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    #selectedOption: string = "jecherche"
    static targets = ["jai", "jecherche", "direction", "apply", "actionList"]
    declare readonly jaiTarget: HTMLElement
    declare readonly jechercheTarget: HTMLElement
    declare readonly directionTarget: HTMLElement
    declare readonly applyTarget: HTMLElement
    declare readonly actionListTarget: HTMLInputElement

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
            const actionButtons = this.jaiTarget.getElementsByTagName("button")
            for (let i = 0; i < actionButtons.length; i++) {
                if (actionButtons[i].getAttribute("aria-pressed") == "true")
                    actionList.push(actionButtons[i].getAttribute("name"))
            }
        }
        if (this.#selectedOption == "jecherche") {
            const actionButtons = this.jechercheTarget.getElementsByTagName("button")
            for (let i = 0; i < actionButtons.length; i++) {
                if (actionButtons[i].getAttribute("aria-pressed") == "true")
                    actionList.push(actionButtons[i].getAttribute("name"))
            }
        }
        this.actionListTarget.value = actionList.join("|")
    }

    changeDirection() {
        this.actionListTarget.value = ""
        this.displayActionList()
        this.apply()
    }
}
