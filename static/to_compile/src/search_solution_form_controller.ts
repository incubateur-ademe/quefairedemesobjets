import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    #selectedOption: string = ""
    static targets = [
        "jai",
        "jecherche",
        "direction",
        "latitudeInput",
        "longitudeInput",
        "actionList",
        "searchForm",
        "reparerInput",
        "groupedActionInput",

        "bbox",

        "searchFormPanel",
        "addressesPanel",
        "backToSearchPanel",
        "detailsAddressPanel",
        "srcDetailsAddress",
        "proposeAddressPanel",
        "headerAddressPanel",

        "expandDetailsButton",
        "collapseDetailsButton",

        "sousCategoryObjetGroup",
        "sousCategoryObjetID",
        "sousCategoryObjetError",

        "adresseGroup",
        "adresseError",

        "advancedFiltersMainPanel",
        "advancedFiltersFormPanel",
        "advancedFiltersSaveButton",
        "advancedFiltersSaveAndSubmitButton",

        "legendMainPanel",
        "legendFormPanel",

        "aProposMainPanel",
        "aProposFormPanel",

        "reparerFilter",

        "carte",

        //FIXME: should be renamed
        "loadingSolutions",
        "addressMissing",
        "NoLocalSolution",
    ]

    declare readonly jaiTarget: HTMLElement
    declare readonly jechercheTarget: HTMLElement
    declare readonly directionTarget: HTMLElement
    declare readonly latitudeInputTarget: HTMLInputElement
    declare readonly longitudeInputTarget: HTMLInputElement
    declare readonly actionListTarget: HTMLInputElement
    declare readonly searchFormTarget: HTMLFormElement
    declare readonly reparerInputTarget: HTMLInputElement
    declare readonly groupedActionInputTargets: HTMLInputElement[]

    declare readonly bboxTarget: HTMLInputElement

    declare readonly hasDirectionTarget: boolean
    declare readonly hasBboxTarget: boolean

    declare readonly searchFormPanelTarget: HTMLElement
    declare readonly addressesPanelTarget: HTMLElement
    declare readonly backToSearchPanelTarget: HTMLElement
    declare readonly detailsAddressPanelTarget: HTMLElement
    declare readonly srcDetailsAddressTarget: HTMLElement
    declare readonly proposeAddressPanelTarget: HTMLElement
    declare readonly headerAddressPanelTarget: HTMLElement

    declare readonly hasProposeAddressPanelTarget: boolean
    declare readonly hasHeaderAddressPanelTarget: boolean

    declare readonly expandDetailsButtonTarget: HTMLElement
    declare readonly collapseDetailsButtonTarget: HTMLElement

    declare readonly sousCategoryObjetGroupTarget: HTMLElement
    declare readonly sousCategoryObjetIDTarget: HTMLInputElement
    declare readonly sousCategoryObjetErrorTarget: HTMLElement

    declare readonly adresseGroupTarget: HTMLElement
    declare readonly adresseErrorTarget: HTMLElement

    declare readonly advancedFiltersMainPanelTarget: HTMLElement
    declare readonly advancedFiltersFormPanelTarget: HTMLElement
    declare readonly advancedFiltersSaveButtonTarget: HTMLElement
    declare readonly advancedFiltersSaveAndSubmitButtonTarget: HTMLElement

    declare readonly legendMainPanelTarget: HTMLElement
    declare readonly legendFormPanelTarget: HTMLElement
    declare readonly hasLegendFormPanelTarget: boolean

    declare readonly aProposMainPanelTarget: HTMLElement
    declare readonly aProposFormPanelTarget: HTMLElement

    declare readonly reparerFilterTargets: HTMLInputElement[]

    declare readonly hasCarteTarget: boolean

    declare readonly loadingSolutionsTarget: HTMLElement
    declare readonly addressMissingTarget: HTMLElement
    declare readonly NoLocalSolutionTarget: HTMLElement

    static values = { isIframe: Boolean }
    declare readonly isIframeValue: boolean

    connect() {
        this.displayActionList()
        if (!this.isIframeValue) {
            this.scrollToContent()
        }
    }

    activeReparerFilters(activate: boolean = true) {
        if (this.#selectedOption == "jai") {
            if (this.reparerInputTarget.checked) {
                this.reparerFilterTargets.forEach((element: HTMLInputElement) => {
                    element.disabled = false
                })
                return
            }
        }
        this.reparerFilterTargets.forEach((element: HTMLInputElement) => {
            element.disabled = true
        })
    }

    activeReparerFiltersCarte(event: Event) {
        const target = event.target as HTMLInputElement
        if (target.value == "reparer") {
            this.reparerFilterTargets.forEach((element: HTMLInputElement) => {
                element.disabled = !target.checked
            })
        }
    }

    scrollToContent() {
        this.searchFormTarget.scrollIntoView()
    }

    hideAddressesPanel() {
        this.backToSearchPanelTarget.classList.add("qfdmo-h-0", "qfdmo-invisible")
        this.addressesPanelTarget.classList.remove("qfdmo-flex-grow")
    }

    showAddressesPanel() {
        this.addressesPanelTarget.classList.add("qfdmo-flex-grow")
        this.addressesPanelTarget.classList.remove("qfdmo-invisible", "qfdmo-h-0")
    }

    backToSearch() {
        this.hideDetails()
        this.#showSearchFormPanel()
        this.hideAddressesPanel()
        this.scrollToContent()
    }

    displayDetails() {
        // mobile
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-0", "qfdmo-invisible")
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-full")
        this.detailsAddressPanelTarget.classList.add("qfdmo-h-1/2")
        if (this.hasProposeAddressPanelTarget) {
            this.proposeAddressPanelTarget.classList.add("qfdmo-h-0", "qfdmo-invisible")
        }
        if (this.hasHeaderAddressPanelTarget)
            this.headerAddressPanelTarget.classList.remove(
                "qfdmo-h-0",
                "qfdmo-invisible",
            )
        this.collapseDetailsButtonTarget.classList.add("qfdmo-hidden")
        this.expandDetailsButtonTarget.classList.remove("qfdmo-hidden")
        // desktop
        this.detailsAddressPanelTarget.classList.add("sm:qfdmo-w-[480]")
        this.detailsAddressPanelTarget.classList.remove("sm:qfdmo-w-full")
        this.detailsAddressPanelTarget.classList.remove("sm:qfdmo-w-0")

        setTimeout(() => {
            this.detailsAddressPanelTarget.focus()
        }, 100)
    }

    updateBboxInput(event) {
        this.bboxTarget.value = JSON.stringify(event.detail)
    }

    hideDetails() {
        document
            .querySelector("[aria-controls=detailsAddressPanel][aria-expanded=true]")
            ?.setAttribute("aria-expanded", "false")

        // mobile
        this.detailsAddressPanelTarget.classList.add("qfdmo-h-0", "qfdmo-invisible")
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-full")
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-1/2")
        if (this.hasProposeAddressPanelTarget) {
            this.proposeAddressPanelTarget.classList.remove(
                "qfdmo-h-0",
                "qfdmo-invisible",
            )
        }
        if (this.hasHeaderAddressPanelTarget)
            this.headerAddressPanelTarget.classList.remove(
                "qfdmo-h-0",
                "qfdmo-invisible",
            )
        // desktop
        this.detailsAddressPanelTarget.classList.add("sm:qfdmo-w-0")
        this.detailsAddressPanelTarget.classList.remove("sm:qfdmo-w-full")
        this.detailsAddressPanelTarget.classList.remove("sm:qfdmo-w-[480]")
    }

    displayFullDetails() {
        // mobile
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-0", "qfdmo-invisible")
        this.detailsAddressPanelTarget.classList.remove("qfdmo-h-1/2")
        this.detailsAddressPanelTarget.classList.add("qfdmo-h-full")
        if (this.hasProposeAddressPanelTarget) {
            this.proposeAddressPanelTarget.classList.add("qfdmo-h-0", "qfdmo-invisible")
        }
        if (this.hasHeaderAddressPanelTarget)
            this.headerAddressPanelTarget.classList.add("qfdmo-h-0", "qfdmo-invisible")
        this.collapseDetailsButtonTarget.classList.remove("qfdmo-hidden")
        this.expandDetailsButtonTarget.classList.add("qfdmo-hidden")
        // desktop
        this.detailsAddressPanelTarget.classList.add("sm:qfdmo-w-full")
        this.detailsAddressPanelTarget.classList.remove("sm:qfdmo-w-0")
        this.detailsAddressPanelTarget.classList.remove("sm:qfdmo-w-[480]")
    }

    displayActeurDetails(event) {
        console.log(event.currentTarget)
        const identifiantUnique = event.currentTarget.dataset.identifiantUnique
        document
            .querySelector(
                "[aria-controls='detailsAddressPanel'][aria-expanded='true']",
            )
            ?.setAttribute("aria-expanded", "false")
        event.currentTarget.setAttribute("aria-expanded", "true")

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
        if (this.hasCarteTarget) {
            params.set("carte", "1")
        }
        const srcDetailsAddress = `/adresse/${identifiantUnique}?${params.toString()}`

        this.srcDetailsAddressTarget.setAttribute("src", srcDetailsAddress)
    }

    displayActionList() {
        if (!this.hasDirectionTarget) {
            return
        }
        const direction = this.directionTarget
        // In "La Carte" mode, the direction is a hidden input
        if (direction instanceof HTMLInputElement) {
            this.#selectedOption = direction.value
            return
        }
        // In form mode, the direction is a fieldset
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
        this.activeReparerFilters()
    }

    apply() {
        const direction = this.directionTarget
        const options = direction.getElementsByTagName("input")
        for (let i = 0; i < options.length; i++) {
            options[i].checked = options[i].value == this.#selectedOption
        }

        let actionList: string[] = []
        if (this.#selectedOption == "jai" || this.#selectedOption == "jecherche") {
            const target =
                this.#selectedOption == "jai" ? this.jaiTarget : this.jechercheTarget
            actionList = this.#setActionList(target)
        }
        this.actionListTarget.value = actionList.join("|")
    }

    #setActionList(target: HTMLElement): string[] {
        const actionInput = target.getElementsByTagName("input")
        let actionList: string[] = []
        for (let i = 0; i < actionInput.length; i++) {
            if (actionInput[i].checked) {
                const name = actionInput[i].getAttribute("name")
                if (name) {
                    actionList.push(name)
                }
            }
        }
        return actionList
    }

    applyLegendGroupedAction(event: Event) {
        const eventTarget = event.target as HTMLInputElement
        this.groupedActionInputTargets.forEach((groupedActionInput) => {
            if (groupedActionInput.value === eventTarget.value) {
                groupedActionInput.checked = eventTarget.checked
            }
        })
        this.advancedSubmit(event)
    }

    changeDirection() {
        this.actionListTarget.value = ""
        this.displayActionList()
        this.apply()
    }

    checkSsCatObjetErrorForm(): boolean {
        let errorExists = false
        if (!this.sousCategoryObjetIDTarget.value) {
            this.sousCategoryObjetGroupTarget.classList.add("fr-input-group--error")
            this.sousCategoryObjetErrorTarget.classList.remove("qfdmo-hidden")
            errorExists = true
        } else {
            this.sousCategoryObjetGroupTarget.classList.remove("fr-input-group--error")
            this.sousCategoryObjetErrorTarget.classList.add("qfdmo-hidden")
        }
        return errorExists
    }

    checkAdresseErrorForm(): boolean {
        let errorExists = false
        if (!this.latitudeInputTarget.value || !this.longitudeInputTarget.value) {
            this.adresseGroupTarget.classList.add("fr-input-group--error")
            this.adresseErrorTarget.classList.remove("qfdmo-hidden")
            errorExists = true
        } else {
            this.adresseGroupTarget.classList.remove("fr-input-group--error")
            this.adresseErrorTarget.classList.add("qfdmo-hidden")
        }
        return errorExists
    }

    #checkErrorForm(): boolean {
        let errorExists = false
        if (this.checkSsCatObjetErrorForm()) errorExists ||= true
        if (this.checkAdresseErrorForm()) errorExists ||= true
        return errorExists
    }

    toggleAdvancedFiltersWithSubmitButton() {
        this.advancedFiltersSaveAndSubmitButtonTarget.classList.remove("qfdmo-hidden")
        this.advancedFiltersSaveButtonTarget.classList.add("qfdmo-hidden")
        this.#toggleAdvancedFilters()
    }

    toggleAdvancedFiltersWithoutSubmitButton() {
        this.advancedFiltersSaveAndSubmitButtonTarget.classList.add("qfdmo-hidden")
        this.advancedFiltersSaveButtonTarget.classList.remove("qfdmo-hidden")
        this.#toggleAdvancedFilters()
    }

    #toggleAdvancedFilters() {
        if (this.advancedFiltersMainPanelTarget.classList.contains("qfdmo-hidden")) {
            this.#showAdvancedFilters()
        } else {
            this.#hideAdvancedFilters()
        }
        this.scrollToContent()
    }

    #showAdvancedFilters() {
        this.advancedFiltersMainPanelTarget.classList.remove("qfdmo-hidden")
        this.advancedFiltersMainPanelTarget.focus()
        setTimeout(() => {
            this.advancedFiltersFormPanelTarget.classList.remove(
                "qfdmo-h-0",
                "qfdmo-invisible",
            )
            this.advancedFiltersFormPanelTarget.classList.add("qfdmo-h-[95%]")
        }, 100)
    }

    #hideAdvancedFilters() {
        this.advancedFiltersFormPanelTarget.classList.remove("qfdmo-h-[95%]")
        this.advancedFiltersFormPanelTarget.classList.add(
            "qfdmo-h-0",
            "qfdmo-invisible",
        )
        setTimeout(() => {
            this.advancedFiltersMainPanelTarget.classList.add("qfdmo-hidden")
        }, 300)
    }

    toggleLegend() {
        if (this.legendMainPanelTarget.classList.contains("qfdmo-hidden")) {
            this.#showLegend()
        } else {
            this.#hideLegend()
        }
        this.scrollToContent()
    }

    #showLegend() {
        this.legendMainPanelTarget.classList.remove("qfdmo-hidden")
        setTimeout(() => {
            this.legendFormPanelTarget.classList.remove("qfdmo-h-0", "qfdmo-invisible")
            this.legendFormPanelTarget.classList.add("qfdmo-h-[95%]")
        }, 100)
    }

    #hideLegend() {
        if (this.hasLegendFormPanelTarget) {
            this.legendFormPanelTarget.classList.remove("qfdmo-h-[95%]")
            this.legendFormPanelTarget.classList.add("qfdmo-h-0", "qfdmo-invisible")
            setTimeout(() => {
                this.legendMainPanelTarget.classList.add("qfdmo-hidden")
            }, 300)
        }
    }

    #showSearchFormPanel() {
        this.searchFormPanelTarget.classList.add("qfdmo-flex-grow")
        this.searchFormPanelTarget.classList.remove("qfdmo-h-0", "qfdmo-invisible")
    }

    #hideSearchFormPanel() {
        this.searchFormPanelTarget.classList.remove("qfdmo-flex-grow")
        this.searchFormPanelTarget.classList.add("qfdmo-h-0", "qfdmo-invisible")
    }

    advancedSubmit(event: Event) {
        const withControls =
            (event.target as HTMLElement).dataset.withControls?.toLowerCase() === "true"
        if (withControls) {
            if (this.#checkErrorForm()) return
        }

        const withoutZone =
            (event.target as HTMLElement).dataset.withoutZone?.toLowerCase() === "true"
        if (withoutZone) {
            if (this.hasBboxTarget) {
                this.bboxTarget.value = ""
            }
        }

        const withDynamicFormPanel =
            (
                event.target as HTMLElement
            ).dataset.withDynamicFormPanel?.toLowerCase() === "true"
        if (withDynamicFormPanel) {
            this.#hideSearchFormPanel()
            this.backToSearchPanelTarget.classList.remove(
                "qfdmo-h-0",
                "qfdmo-invisible",
            )
            this.showAddressesPanel()
            this.scrollToContent()
        }

        this.loadingSolutionsTarget.classList.remove("qfdmo-hidden")
        this.addressMissingTarget.classList.add("qfdmo-hidden")
        this.NoLocalSolutionTarget.classList.add("qfdmo-hidden")
        this.#hideAdvancedFilters()
        this.#hideLegend()

        let submitEvent = new Event("submit", { bubbles: true, cancelable: true })
        setTimeout(() => {
            this.searchFormTarget.dispatchEvent(submitEvent)
        }, 300)
    }

    toggleAPropos() {
        if (this.aProposMainPanelTarget.classList.contains("qfdmo-hidden")) {
            this.#showAPropos()
        } else {
            this.#hideAPropos()
        }
        this.scrollToContent()
    }

    #showAPropos() {
        this.aProposMainPanelTarget.classList.remove("qfdmo-hidden")
        setTimeout(() => {
            this.aProposFormPanelTarget.classList.remove("qfdmo-h-0", "qfdmo-invisible")
            this.aProposFormPanelTarget.classList.add("qfdmo-h-[95%]")
        }, 100)
    }

    #hideAPropos() {
        this.aProposFormPanelTarget.classList.remove("qfdmo-h-[95%]")
        this.aProposFormPanelTarget.classList.add("qfdmo-h-0", "qfdmo-invisible")
        setTimeout(() => {
            this.aProposMainPanelTarget.classList.add("qfdmo-hidden")
        }, 300)
    }
}
