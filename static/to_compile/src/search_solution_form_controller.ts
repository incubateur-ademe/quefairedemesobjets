import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    #selectedOption: string = "jecherche"
    static targets = [
        "jai",
        "jecherche",
        "direction",
        "actionList",
        "searchForm",
        "searchFormPanel",
        "adressesPanel",
        "backToSearchPanel",
        "detailsAddressPanel",
        "srcDetailsAddress",
    ]

    declare readonly jaiTarget: HTMLElement
    declare readonly jechercheTarget: HTMLElement
    declare readonly directionTarget: HTMLElement
    declare readonly actionListTarget: HTMLInputElement

    declare readonly searchFormPanelTarget: HTMLElement
    // var search_form_div = document.getElementById("search_form_div"); // searchFormPanel
    // var adresses = document.getElementById("adresses");
    // let search_summary = document.getElementById("search_summary");
    declare readonly adressesPanelTarget: HTMLElement
    declare readonly backToSearchPanelTarget: HTMLElement
    declare readonly searchFormTarget: HTMLFormElement
    declare readonly detailsAddressPanelTarget: HTMLElement
    declare readonly srcDetailsAddressTarget: HTMLElement

    connect() {
        this.displayActionList()
        this.scrollToContent()
    }

    scrollToContent() {
        this.searchFormTarget.scrollIntoView()
    }

    searchAdresses() {
        // adresses.classList.add("qfdmo-flex-grow");
        // search_summary.classList.remove("qfdmo-h-0");
        // search_form_div.classList.remove("qfdmo-flex-grow");
        this.loadingSolutions()
        this.searchFormPanelTarget.classList.remove("qfdmo-flex-grow")
        this.backToSearchPanelTarget.classList.remove("qfdmo-h-0")
        this.adressesPanelTarget.classList.add("qfdmo-flex-grow")
        this.scrollToContent()
    }

    backToSearch() {
        // adresses.classList.remove("qfdmo-flex-grow");
        // search_summary.classList.add("qfdmo-h-0");
        // search_form_div.classList.add("qfdmo-flex-grow");
        this.hideDetails()
        this.searchFormPanelTarget.classList.add("qfdmo-flex-grow")
        this.backToSearchPanelTarget.classList.add("qfdmo-h-0")
        this.adressesPanelTarget.classList.remove("qfdmo-flex-grow")
        this.scrollToContent()
    }

    displayDetail() {
        // mobile
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-0")
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-full")
        this.detailsAddressPanelTarget.classList.add("qfdmo-h-1/2")
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
        // desktop
        this.detailsAddressPanelTarget.classList.add("md:qfdmo-w-full")
        this.detailsAddressPanelTarget.classList.remove("md:qfdmo-w-0")
        this.detailsAddressPanelTarget.classList.remove("md:qfdmo-w-[480]")
    }

    setSrcDetailsAddress({ detail: { src } }) {
        this.srcDetailsAddressTarget.setAttribute("src", src)
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
        this.dispatch("loadingSolutions", { detail: {} })
        this.searchFormTarget.submit()
    }

    loadingSolutions() {
        this.dispatch("loadingSolutions", { detail: {} })
    }
}
