import { ClickOutsideController } from "stimulus-use"

export default class AutocompleteController extends ClickOutsideController<HTMLElement> {
  static targets = ["option", "input", "hiddenInput", "results"]
  static values = {
    endpointUrl: String,
    turboFrameId: String,
    limit: String,
    showOnFocus: { type: Boolean, default: false },
  }
  declare readonly optionTargets: HTMLElement[]
  declare readonly resultsTarget: HTMLElement
  declare readonly turboFrameIdValue: string
  declare readonly endpointUrlValue: string
  declare readonly limitValue: string
  declare readonly showOnFocusValue: boolean
  declare readonly inputTarget: HTMLInputElement
  declare readonly hiddenInputTarget: HTMLInputElement

  currentIndex = -1

  connect() {
    this.#hideListbox()
  }

  clickOutside(event) {
    this.#hideListbox()
  }

  focus(event) {
    if (this.showOnFocusValue && this.inputTarget.value) {
      this.#loadResults(this.inputTarget.value)
    }
  }

  search(event) {
    this.#loadResults(event.target.value)
  }

  #loadResults(query: string) {
    const nextUrl = new URL(this.endpointUrlValue, window.location.origin)
    nextUrl.searchParams.set("q", query)
    nextUrl.searchParams.set("turbo_frame_id", this.turboFrameIdValue)
    nextUrl.searchParams.set("limit", this.limitValue)
    this.resultsTarget.setAttribute("src", nextUrl.toString())
    this.#showListbox()
  }

  navigate(event: KeyboardEvent) {
    const key = event.key

    // Allow Tab key to work normally for keyboard navigation
    if (key === "Tab") {
      this.#hideListbox()
      return
    }

    switch (key) {
      case "ArrowDown":
        event.preventDefault()
        // Alt+Down: Open listbox without moving focus
        if (event.altKey) {
          this.#showListbox()
          return
        }
        // Down Arrow: Opens the listbox if closed and moves focus to first option
        // If already open, moves focus to next option
        if (this.resultsTarget.hidden) {
          this.#openListboxAndFocus(0)
        } else {
          this.#moveFocus(1)
        }
        break

      case "ArrowUp":
        event.preventDefault()
        // Up Arrow: Opens the listbox if closed and moves focus to last option
        // If already open, moves focus to previous option
        if (this.resultsTarget.hidden) {
          this.#openListboxAndFocus(this.optionTargets.length - 1)
        } else {
          this.#moveFocus(-1)
        }
        break

      case "Enter":
        event.preventDefault()
        // Enter: Accepts the focused value, closes listbox
        this.commitSelection()
        break

      case "Escape":
        event.preventDefault()
        // Escape: Closes the listbox if displayed, otherwise clears the combobox
        this.#escapeAction()
        break

      case "Home":
        // Home: Moves focus to first option (if listbox is open)
        if (this.#isListboxOpenWithOptions()) {
          event.preventDefault()
          this.#setVisualFocus(0)
        }
        break

      case "End":
        // End: Moves focus to last option (if listbox is open)
        if (this.#isListboxOpenWithOptions()) {
          event.preventDefault()
          this.#setVisualFocus(this.optionTargets.length - 1)
        }
        break
    }
  }

  optionTargetConnected() {
    this.#refreshOptions()
  }

  #refreshOptions() {
    this.currentIndex = -1
  }

  #isListboxOpenWithOptions(): boolean {
    return !this.resultsTarget.hidden && this.optionTargets.length > 0
  }

  #openListboxAndFocus(index: number) {
    this.#showListbox()
    if (this.optionTargets.length > 0) {
      this.#setVisualFocus(index)
    }
  }

  #getLinkFromOption(option: HTMLElement): HTMLAnchorElement | null {
    return option.querySelector("a")
  }

  #moveFocus(direction: number) {
    if (this.optionTargets.length === 0) {
      return
    }

    // Calculate new index with wrapping
    let newIndex = this.currentIndex + direction

    // Wrap around
    if (newIndex < 0) {
      newIndex = this.optionTargets.length - 1
    } else if (newIndex >= this.optionTargets.length) {
      newIndex = 0
    }

    this.#setVisualFocus(newIndex)
  }

  #setVisualFocus(index: number) {
    if (index < 0 || index >= this.optionTargets.length) {
      return
    }

    this.currentIndex = index
    const currentOption = this.optionTargets[this.currentIndex]

    // Remove aria-selected from all options
    this.#removeSelection()

    // Set aria-selected on current option
    currentOption.setAttribute("aria-selected", "true")

    // If option contains a link, focus it. Otherwise keep focus on input
    const link = this.#getLinkFromOption(currentOption)
    if (link) {
      link.focus()
    } else {
      // Keep focus on input, update aria-activedescendant
      this.inputTarget.focus()
    }

    this.inputTarget.setAttribute("aria-activedescendant", currentOption.id || "")

    // Scroll into view if needed
    currentOption.scrollIntoView({ block: "nearest", behavior: "smooth" })
  }

  commitSelection(event?) {
    let selected = this.optionTargets[this.currentIndex]
    if (event?.target) {
      selected = event.target.closest('[data-next-autocomplete-target="option"]')
    }
    if (!selected) return

    const link = this.#getLinkFromOption(selected)

    // Link mode: keyboard Enter triggers the link
    if (!event && link) {
      this.#hideListbox()
      link.click()
      return
    }

    // Form mode: populate the form fields and emit commit event
    const value = selected.dataset.value?.trim() || ""
    const selectedValue = selected.dataset.selectedValue?.trim() || ""

    this.hiddenInputTarget.value = value
    this.inputTarget.value = selectedValue
    this.#hideListbox()

    const commitEvent = new CustomEvent("next-autocomplete:commit", {
      bubbles: true,
      detail: { option: selected, value, selectedValue },
    })
    this.element.dispatchEvent(commitEvent)
  }

  #escapeAction() {
    if (!this.resultsTarget.hidden) {
      this.#hideListbox()
    } else {
      this.inputTarget.value = ""
    }
  }

  #showListbox() {
    this.resultsTarget.hidden = false
    this.inputTarget.setAttribute("aria-expanded", "true")
  }

  #removeSelection() {
    this.optionTargets.forEach((opt) => {
      opt.removeAttribute("aria-selected")
    })
  }

  #hideListbox() {
    this.resultsTarget.hidden = true
    this.inputTarget.setAttribute("aria-expanded", "false")
    this.inputTarget.removeAttribute("aria-activedescendant")
    this.#removeSelection()
    this.currentIndex = -1
  }
}
