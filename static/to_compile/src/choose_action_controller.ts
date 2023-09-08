import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    static targets = [
        "jai",
        "jecherche",
        "overwrittenDirection",
        "direction",
        "apply",
        "actionList",
    ]
    declare readonly jaiTarget: HTMLElement
    declare readonly jechercheTarget: HTMLElement
    declare readonly overwrittenDirectionTarget: HTMLElement
    declare readonly directionTarget: HTMLElement
    declare readonly applyTarget: HTMLElement
    declare readonly actionListTarget: HTMLInputElement

    connect() {
        this.displayActionList()
    }

    displayActionList() {
        const overwrittenDirection = this.overwrittenDirectionTarget
        const options = overwrittenDirection.getElementsByTagName("input")
        for (let i = 0; i < options.length; i++) {
            if (options[i].checked && options[i].value == "jai") {
                this.jechercheTarget.hidden = true
                this.jaiTarget.hidden = false
            }
            if (options[i].checked && options[i].value == "jecherche") {
                this.jechercheTarget.hidden = false
                this.jaiTarget.hidden = true
            }
        }
    }

    apply() {
        const overwrittenDirection = this.overwrittenDirectionTarget
        const overwrittenOptions = overwrittenDirection.getElementsByTagName("input")
        let checkedValue = "jai"
        for (let i = 0; i < overwrittenOptions.length; i++) {
            if (overwrittenOptions[i].checked)
                checkedValue = overwrittenOptions[i].value
        }

        const direction = this.directionTarget
        const options = direction.getElementsByTagName("input")
        for (let i = 0; i < options.length; i++) {
            if (options[i].value == checkedValue) options[i].checked = true
            else options[i].checked = false
        }

        let actionList = []
        if (checkedValue == "jai") {
            const actionButtons = this.jaiTarget.getElementsByTagName("button")
            for (let i = 0; i < actionButtons.length; i++) {
                if (actionButtons[i].getAttribute("aria-pressed") == "true")
                    actionList.push(actionButtons[i].getAttribute("name"))
            }
        }
        if (checkedValue == "jecherche") {
            const actionButtons = this.jechercheTarget.getElementsByTagName("button")
            for (let i = 0; i < actionButtons.length; i++) {
                if (actionButtons[i].getAttribute("aria-pressed") == "true")
                    actionList.push(actionButtons[i].getAttribute("name"))
            }
        }
        this.actionListTarget.value = actionList.join("|")

        overwrittenOptions[0].form.submit()
    }

    changeDirection() {
        this.actionListTarget.value = ""
        this.actionListTarget.form.submit()
    }
}
