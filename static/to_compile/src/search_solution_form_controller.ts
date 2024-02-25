import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    #selectedOption: string = "jecherche"
    static targets = [
        "jai",
        "jecherche",
        "direction",
        "latitudeInput",
        "longitudeInput",
        "actionList",
        "searchForm",

        "searchFormPanel",
        "addressesPanel",
        "backToSearchPanel",
        "detailsAddressPanel",
        "srcDetailsAddress",
        "proposeAddressPanel",
        "headerAddressPanel",

        "expandDetailsButton",
        "collapseDetailsButton",

        //FIXME: should be renamed
        "loadingSolutions",
        "addressMissing",
        "NoLocalSolution",
    ]

    declare readonly jaiTarget: HTMLElement
    declare readonly jechercheTarget: HTMLElement
    declare readonly directionTarget: HTMLElement
    declare readonly actionListTarget: HTMLInputElement
    declare readonly latitudeInputTarget: HTMLInputElement
    declare readonly longitudeInputTarget: HTMLInputElement

    declare readonly searchFormPanelTarget: HTMLElement
    declare readonly addressesPanelTarget: HTMLElement
    declare readonly backToSearchPanelTarget: HTMLElement
    declare readonly searchFormTarget: HTMLFormElement
    declare readonly detailsAddressPanelTarget: HTMLElement
    declare readonly srcDetailsAddressTarget: HTMLElement
    declare readonly proposeAddressPanelTarget: HTMLElement
    declare readonly headerAddressPanelTarget: HTMLElement
    declare readonly expandDetailsButtonTarget: HTMLElement
    declare readonly collapseDetailsButtonTarget: HTMLElement
    declare readonly loadingSolutionsTarget: HTMLElement
    declare readonly addressMissingTarget: HTMLElement
    declare readonly NoLocalSolutionTarget: HTMLElement

    loadingSolutions() {
        this.loadingSolutionsTarget.classList.remove("qfdmo-hidden")
        if (this.addressMissingTarget !== undefined)
            this.addressMissingTarget.classList.add("qfdmo-hidden")
        this.NoLocalSolutionTarget.classList.add("qfdmo-hidden")
    }

    connect() {
        this.displayActionList()
        this.scrollToContent()
    }

    scrollToContent() {
        this.searchFormTarget.scrollIntoView()
    }

    searchAdresses() {
        this.loadingSolutions()
        this.searchFormPanelTarget.classList.remove("qfdmo-flex-grow")
        this.backToSearchPanelTarget.classList.remove("qfdmo-h-0")
        this.addressesPanelTarget.classList.add("qfdmo-flex-grow")
        this.scrollToContent()
    }

    backToSearch() {
        this.hideDetails()
        this.searchFormPanelTarget.classList.add("qfdmo-flex-grow")
        this.backToSearchPanelTarget.classList.add("qfdmo-h-0")
        this.addressesPanelTarget.classList.remove("qfdmo-flex-grow")
        this.scrollToContent()
    }

    displayDetails() {
        // mobile
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-0")
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-full")
        this.detailsAddressPanelTarget.classList.add("qfdmo-h-1/2")
        this.proposeAddressPanelTarget.classList.add("qfdmo-h-0")
        this.headerAddressPanelTarget.classList.remove("qfdmo-h-0")
        this.collapseDetailsButtonTarget.classList.add("qfdmo-hidden")
        this.expandDetailsButtonTarget.classList.remove("qfdmo-hidden")
        // desktop
        this.detailsAddressPanelTarget.classList.add("md:qfdmo-w-[480]")
        this.detailsAddressPanelTarget.classList.remove("md:qfdmo-w-full")
        this.detailsAddressPanelTarget.classList.remove("md:qfdmo-w-0")
    }

    hideDetails() {
        // mobile
        this.detailsAddressPanelTarget.classList.add("qfdmo-h-0")
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-full")
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-1/2")
        this.proposeAddressPanelTarget.classList.remove("qfdmo-h-0")
        this.headerAddressPanelTarget.classList.remove("qfdmo-h-0")
        // desktop
        this.detailsAddressPanelTarget.classList.add("md:qfdmo-w-0")
        this.detailsAddressPanelTarget.classList.remove("md:qfdmo-w-full")
        this.detailsAddressPanelTarget.classList.remove("md:qfdmo-w-[480]")
    }

    displayFullDetails() {
        // mobile
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-0")
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-1/2")
        this.detailsAddressPanelTarget.classList.add("qfdmo-h-full")
        this.proposeAddressPanelTarget.classList.add("qfdmo-h-0")
        this.headerAddressPanelTarget.classList.add("qfdmo-h-0")
        this.collapseDetailsButtonTarget.classList.remove("qfdmo-hidden")
        this.expandDetailsButtonTarget.classList.add("qfdmo-hidden")
        // desktop
        this.detailsAddressPanelTarget.classList.add("md:qfdmo-w-full")
        this.detailsAddressPanelTarget.classList.remove("md:qfdmo-w-0")
        this.detailsAddressPanelTarget.classList.remove("md:qfdmo-w-[480]")
    }

    displayActeurDetails(event) {
        let identifiantUnique = event.currentTarget.dataset.identifiantUnique
        this.setSrcDetailsAddress({ detail: { identifiantUnique } })
        this.displayDetails()
    }
    setSrcDetailsAddress({ detail: { identifiantUnique } }) {
        const latitude = this.latitudeInputTarget.value
        const longitude = this.longitudeInputTarget.value

        const params = new URLSearchParams()
        params.set("direction", this.#selectedOption)
        params.set("latitude", latitude)
        params.set("longitude", longitude)
        const srcDetailsAddress = `/adresse/${identifiantUnique}?${params.toString()}`

        this.srcDetailsAddressTarget.setAttribute("src", srcDetailsAddress)
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

    submitForm() {
        this.loadingSolutionsTarget.classList.remove("qfdmo-hidden")
        this.dispatch("loadingSolutions", { detail: {} })
        let event = new Event("submit", { bubbles: true, cancelable: true })

        setTimeout(() => {
            this.searchFormTarget.dispatchEvent(event)
        }, 300)
    }
}
