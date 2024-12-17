import { Controller } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"
import { clearActivePinpoints, removeHash } from "./helpers"

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
    "acteurDetailsPanel",
    "proposeAddressPanel",
    "headerAddressPanel",

    "collapseDetailsButton",

    "sousCategoryObjetGroup",
    "sousCategoryObjetID",
    "sousCategoryObjetError",

    "adresseGroup",
    "adresseError",

    "advancedFiltersMainPanel",
    "advancedFiltersSaveButton",
    "advancedFiltersSaveAndSubmitButton",

    "legendMainPanel",
    "legendFormPanel",

    "aProposMainPanel",
    "aProposFormPanel",

    "reparerFilter",

    "carte",
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
  declare readonly acteurDetailsPanelTarget: HTMLElement
  declare readonly proposeAddressPanelTarget: HTMLElement
  declare readonly headerAddressPanelTarget: HTMLElement

  declare readonly hasProposeAddressPanelTarget: boolean
  declare readonly hasHeaderAddressPanelTarget: boolean

  declare readonly collapseDetailsButtonTarget: HTMLElement

  declare readonly sousCategoryObjetGroupTarget: HTMLElement
  declare readonly sousCategoryObjetIDTarget: HTMLInputElement
  declare readonly sousCategoryObjetErrorTarget: HTMLElement

  declare readonly adresseGroupTarget: HTMLElement
  declare readonly adresseErrorTarget: HTMLElement

  declare readonly advancedFiltersMainPanelTarget: HTMLElement
  declare readonly advancedFiltersSaveButtonTarget: HTMLElement
  declare readonly advancedFiltersSaveAndSubmitButtonTarget: HTMLElement

  declare readonly legendMainPanelTarget: HTMLElement
  declare readonly legendFormPanelTarget: HTMLElement
  declare readonly hasLegendFormPanelTarget: boolean

  declare readonly aProposMainPanelTarget: HTMLElement
  declare readonly aProposFormPanelTarget: HTMLElement

  declare readonly reparerFilterTargets: HTMLInputElement[]

  declare readonly hasCarteTarget: boolean

  static values = { isIframe: Boolean }
  declare readonly isIframeValue: boolean

  connect() {
    this.displayActionList()
    window.addEventListener("hashchange", this.#setActiveActeur.bind(this))
    // Prevents the leaflet map to move when the user moves panel
    this.acteurDetailsPanelTarget.addEventListener("touchmove", (event) =>
      event.stopPropagation(),
    )

    if (!this.isIframeValue) {
      this.scrollToContent()
    }
  }

  #setActiveActeur(event?: HashChangeEvent) {
    const uuid = event
      ? new URL(event.newURL).hash.substring(1)
      : window.location.hash.substring(1)
    if (uuid) {
      this.displayActeur(uuid)
      this.dispatch("captureInteraction")
    } else {
      this.hideActeurDetailsPanel()
    }
  }

  activeReparerFilters(activate: boolean = true) {
    // Carte mode
    this.activeReparerFiltersCarte()

    // Form mode
    this.activeReparerFiltersForm()
  }

  activeReparerFiltersForm() {
    if (this.groupedActionInputTargets.length == 0) {
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
  }

  activeReparerFiltersCarte() {
    if (this.groupedActionInputTargets.length > 0) {
      let reparerFilterIsDisplayed = false
      this.groupedActionInputTargets.forEach((groupedActionInput) => {
        if (groupedActionInput.value == "reparer") {
          reparerFilterIsDisplayed = true
          this.reparerFilterTargets.forEach((element: HTMLInputElement) => {
            element.disabled = !groupedActionInput.checked
          })
        }
        return reparerFilterIsDisplayed
      })
      if (!reparerFilterIsDisplayed) {
        this.reparerFilterTargets.forEach((element: HTMLInputElement) => {
          element.disabled = true
        })
      }
    }
  }

  scrollToContent() {
    this.searchFormTarget.scrollIntoView({ behavior: "smooth" })
  }

  #hideAddressesPanel() {
    this.backToSearchPanelTarget.dataset.visible = "false"
    this.addressesPanelTarget.dataset.visible = "false"
  }

  #showAddressesPanel() {
    this.addressesPanelTarget.dataset.visible = "true"
  }

  backToSearch() {
    this.hideActeurDetailsPanel()
    this.#showSearchFormPanel()
    this.#hideAddressesPanel()
    this.scrollToContent()
  }

  updateBboxInput(event) {
    this.bboxTarget.value = JSON.stringify(event.detail)
  }

  #showActeurDetailsPanel() {
    if (this.acteurDetailsPanelTarget.ariaHidden !== "false") {
      this.acteurDetailsPanelTarget.ariaHidden = "false"
    }

    this.acteurDetailsPanelTarget.dataset.exitAnimationEnded = "false"
    this.acteurDetailsPanelTarget.scrollIntoView()
  }

  hideActeurDetailsPanel() {
    removeHash()
    document
      .querySelector("[aria-controls=acteurDetailsPanel][aria-expanded=true]")
      ?.setAttribute("aria-expanded", "false")
    this.acteurDetailsPanelTarget.ariaHidden = "true"
    this.acteurDetailsPanelTarget.addEventListener(
      "animationend",
      () => {
        this.acteurDetailsPanelTarget.dataset.exitAnimationEnded = "true"
      },
      { once: true },
    )
    clearActivePinpoints()
  }

  displayDigitalActeur(event) {
    const uuid = event.currentTarget.dataset.uuid
    window.location.hash = uuid
    document
      .querySelector("[aria-controls='acteurDetailsPanel'][aria-expanded='true']")
      ?.setAttribute("aria-expanded", "false")
    event.currentTarget.setAttribute("aria-expanded", "true")
    this.#showActeurDetailsPanel()
  }

  displayActeur(uuid: string) {
    const latitude = this.latitudeInputTarget.value
    const longitude = this.longitudeInputTarget.value

    const params = new URLSearchParams()
    params.set("direction", this.#selectedOption)
    params.set("latitude", latitude)
    params.set("longitude", longitude)
    if (this.hasCarteTarget) {
      params.set("carte", "1")
    }
    const acteurDetailPath = `/adresse_details/${uuid}?${params.toString()}`
    Turbo.visit(acteurDetailPath, { frame: "acteur-detail" })
    this.#showActeurDetailsPanel()
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
    // Mode Carte
    this.activeReparerFiltersCarte()
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
      this.sousCategoryObjetErrorTarget.classList.remove("qf-hidden")
      errorExists = true
    } else {
      this.sousCategoryObjetGroupTarget.classList.remove("fr-input-group--error")
      this.sousCategoryObjetErrorTarget.classList.add("qf-hidden")
    }
    return errorExists
  }

  checkAdresseErrorForm(): boolean {
    let errorExists = false
    if (!this.latitudeInputTarget.value || !this.longitudeInputTarget.value) {
      this.adresseGroupTarget.classList.add("fr-input-group--error")
      this.adresseErrorTarget.classList.remove("qf-hidden")
      errorExists = true
    } else {
      this.adresseGroupTarget.classList.remove("fr-input-group--error")
      this.adresseErrorTarget.classList.add("qf-hidden")
    }
    return errorExists
  }

  #checkErrorForm(): boolean {
    let errorExists = false
    if (this.checkSsCatObjetErrorForm()) errorExists ||= true
    if (this.checkAdresseErrorForm()) errorExists ||= true
    return errorExists
  }

  closeAdvancedFilters() {
    this.advancedFiltersSaveAndSubmitButtonTarget.classList.remove("qf-hidden")
    this.advancedFiltersSaveButtonTarget.classList.add("qf-hidden")
    this.#hideAdvancedFilters()
    this.scrollToContent()
  }

  toggleAdvancedFilters() {
    this.advancedFiltersSaveAndSubmitButtonTarget.classList.remove("qf-hidden")
    this.advancedFiltersSaveButtonTarget.classList.add("qf-hidden")
    if (this.advancedFiltersMainPanelTarget.dataset.visible === "false") {
      this.#showAdvancedFilters()
    } else {
      this.#hideAdvancedFilters()
    }
    this.scrollToContent()
  }

  #showAdvancedFilters() {
    this.advancedFiltersMainPanelTarget.dataset.visible = "true"
  }

  #hideAdvancedFilters() {
    if (this.advancedFiltersMainPanelTarget.dataset.visible == "false") {
      return
    }

    this.advancedFiltersMainPanelTarget.dataset.visible = "exit"
    this.advancedFiltersMainPanelTarget.addEventListener(
      "animationend",
      () => {
        this.advancedFiltersMainPanelTarget.dataset.visible = "false"
      },
      { once: true },
    )
  }

  showLegend() {
    this.legendMainPanelTarget.classList.remove("qf-hidden")
    setTimeout(() => {
      this.legendFormPanelTarget.classList.remove("qf-h-0", "qf-invisible")
      this.legendFormPanelTarget.classList.add("qf-h-[95%]")
    }, 100)
    this.scrollToContent()
  }

  hideLegend() {
    if (this.hasLegendFormPanelTarget) {
      this.legendFormPanelTarget.classList.remove("qf-h-[95%]")
      this.legendFormPanelTarget.classList.add("qf-h-0", "qf-invisible")
      setTimeout(() => {
        this.legendMainPanelTarget.classList.add("qf-hidden")
      }, 300)
    }
  }

  #showSearchFormPanel() {
    this.element.dataset.searchFormVisible = ""
    this.searchFormPanelTarget.classList.add("qf-flex-grow")
    this.searchFormPanelTarget.classList.remove("qf-h-0", "qf-invisible")
  }

  #hideSearchFormPanel() {
    delete this.element.dataset.searchFormVisible
    this.searchFormPanelTarget.dataset.visible = "false"
    this.searchFormPanelTarget.classList.remove("qf-flex-grow")
    this.searchFormPanelTarget.classList.add("qf-h-0", "qf-invisible")
  }

  advancedSubmit(event: Event) {
    this.hideActeurDetailsPanel()
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
      (event.target as HTMLElement).dataset.withDynamicFormPanel?.toLowerCase() ===
      "true"

    if (withDynamicFormPanel) {
      this.#hideSearchFormPanel()
      this.backToSearchPanelTarget.dataset.visible = "true"
      this.#showAddressesPanel()
      this.scrollToContent()
    }

    this.#hideAdvancedFilters()
    this.hideLegend()

    let submitEvent = new Event("submit", { bubbles: true, cancelable: true })
    this.searchFormTarget.dispatchEvent(submitEvent)
  }

  toggleAPropos() {
    if (this.aProposMainPanelTarget.dataset.visible === "true") {
      this.#hideAPropos()
    } else {
      this.#showAPropos()
    }
    this.scrollToContent()
  }

  #showAPropos() {
    this.aProposMainPanelTarget.dataset.visible = "true"
  }

  #hideAPropos() {
    this.aProposMainPanelTarget.dataset.visible = "exit"
    this.aProposMainPanelTarget.addEventListener(
      "animationend",
      () => {
        this.aProposMainPanelTarget.dataset.visible = "false"
      },
      { once: true },
    )
  }
}
