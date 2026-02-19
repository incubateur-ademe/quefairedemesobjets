import { ClickOutsideController } from "stimulus-use"

export default class AutocompleteController extends ClickOutsideController<HTMLElement> {
  static targets = ["option", "input", "hiddenInput", "results"]
  static values = {
    endpointUrl: String,
    turboFrameId: String,
    limit: String,
  }
  declare readonly optionTargets: HTMLElement[]
  declare readonly resultsTarget: HTMLElement
  declare readonly turboFrameIdValue: string
  declare readonly endpointUrlValue: string
  declare readonly limitValue: string
  declare readonly inputTarget: HTMLInputElement
  declare readonly hiddenInputTarget: HTMLInputElement

  currentIndex = -1

  connect() {
    this.hideListbox()
  }

  clickOutside(event) {
    this.hideListbox()
  }

  search(event) {
    const query = event.target.value
    const nextUrl = new URL(this.endpointUrlValue, window.location.origin)
    nextUrl.searchParams.set("q", query)
    // TODO : set query params key from django view
    nextUrl.searchParams.set("turbo_frame_id", this.turboFrameIdValue)
    nextUrl.searchParams.set("limit", this.limitValue)
    this.resultsTarget.setAttribute("src", nextUrl.toString())
    this.showListbox()
  }

  navigate(event: KeyboardEvent) {
    const key = event.key

    switch (key) {
      case "ArrowDown":
        event.preventDefault()
        if (event.altKey) {
          this.showListbox()
          return
        }
        this.moveFocus(1)
        break

      case "ArrowUp":
        event.preventDefault()
        this.moveFocus(-1)
        break

      case "Enter":
        event.preventDefault()
        this.commitSelection()
        break

      case "Escape":
        event.preventDefault()
        this.escapeAction()
        break
    }
  }

  optionTargetConnected() {
    this.refreshOptions()
  }

  refreshOptions() {
    this.currentIndex = -1
  }

  moveFocus(direction: number) {
    if (this.optionTargets.length === 0) {
      this.showListbox()
      return
    }

    this.currentIndex =
      (this.currentIndex + direction + this.optionTargets.length) %
      this.optionTargets.length
    const currentOption = this.optionTargets[this.currentIndex]

    this.#blurOptions()
    currentOption.focus()
    this.inputTarget.setAttribute("aria-activedescendant", currentOption.id || "")
    this.showListbox()
  }

  commitSelection(event?) {
    let selected = this.optionTargets[this.currentIndex]
    if (event?.target) {
      selected = event.target
    }
    if (!selected) return

    this.hiddenInputTarget.value = selected.dataset.value?.trim() || ""
    this.inputTarget.value = selected.dataset.selectedValue?.trim() || ""
    this.hideListbox()
  }

  escapeAction() {
    if (!this.resultsTarget.hidden) {
      this.hideListbox()
    } else {
      this.inputTarget.value = ""
    }
  }

  showListbox() {
    this.resultsTarget.hidden = false
    this.inputTarget.setAttribute("aria-expanded", "true")
  }

  #blurOptions() {
    this.optionTargets.forEach((opt) => opt.blur())
  }

  hideListbox() {
    this.resultsTarget.hidden = true
    this.inputTarget.setAttribute("aria-expanded", "false")
    this.inputTarget.removeAttribute("aria-activedescendant")
    this.#blurOptions()
    this.currentIndex = -1
  }
}
