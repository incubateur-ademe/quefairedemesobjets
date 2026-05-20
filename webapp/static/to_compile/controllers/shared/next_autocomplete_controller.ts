import { ClickOutsideController } from "stimulus-use"
import { computeAvailableHeight } from "../../js/helpers"

export default class AutocompleteController extends ClickOutsideController<HTMLElement> {
  static targets = ["option", "input", "hiddenInput", "results"]
  static values = {
    endpointUrl: String,
    turboFrameId: String,
    limit: String,
    showOnFocus: { type: Boolean, default: false },
    eventName: { type: String, default: "" },
    fieldName: { type: String, default: "" },
  }
  declare readonly optionTargets: HTMLElement[]
  declare readonly resultsTarget: HTMLElement
  declare readonly turboFrameIdValue: string
  declare readonly endpointUrlValue: string
  declare readonly limitValue: string
  declare readonly showOnFocusValue: boolean
  declare readonly eventNameValue: string
  declare readonly fieldNameValue: string
  declare readonly inputTarget: HTMLInputElement
  declare readonly hiddenInputTarget: HTMLInputElement
  declare readonly hasHiddenInputTarget: boolean

  currentIndex = -1
  // Tracks whether the current input value came from the user typing (true)
  // or from a commit / external programmatic write / page load (false). We
  // suppress reopening the listbox on refocus when the value was not typed
  // by the user — the value was set for them; reopening would be ghosty.
  //
  // A boolean is safer than snapshotting the value because external writers
  // (state.ts mirroring sessionStorage into the input on outlet-connect, for
  // instance) update `inputTarget.value` directly and would not keep a
  // value snapshot in sync.
  #userIsTyping = false

  // Margin between the bottom of the dropdown and the bottom of the document
  // body, so the dropdown never touches the very edge of the iframe.
  static #LISTBOX_BOTTOM_MARGIN_PX = 16

  #boundReposition = () => this.#positionListbox()

  connect() {
    this.#hideListbox()
    window.addEventListener("resize", this.#boundReposition)
    window.addEventListener("scroll", this.#boundReposition, { passive: true })
  }

  disconnect() {
    window.removeEventListener("resize", this.#boundReposition)
    window.removeEventListener("scroll", this.#boundReposition)
  }

  clickOutside(event) {
    this.#hideListbox()
  }

  focus(event) {
    if (!this.showOnFocusValue) return
    // Empty input: always open so the synthetic top option (e.g. "Autour de
    // moi" for the carte address combobox) is reachable on the very first
    // focus. The backend returns it for sub-MIN_QUERY_LENGTH queries.
    if (!this.inputTarget.value) {
      this.#loadResults("")
      return
    }
    // Non-empty input: only reopen when the user was mid-typing. A value that
    // was set programmatically (commit, state restore, server render) is
    // treated as already committed and must not re-open on refocus.
    if (!this.#userIsTyping) return
    this.#loadResults(this.inputTarget.value)
  }

  search(event) {
    // Typing means the user is actively searching: clear the "committed" flag
    // so refocus after a blur reopens the listbox.
    this.#userIsTyping = true
    this.#loadResults(event.target.value)
  }

  resultClick(event: MouseEvent) {
    if (!this.eventNameValue) return
    const li = event.currentTarget as HTMLElement
    const position = this.optionTargets.indexOf(li) + 1
    const inputText = this.inputTarget.value
    const anchor = this.#getLinkFromOption(li)
    const linkData = anchor ? { ...anchor.dataset } : {}

    this.element.dispatchEvent(
      new CustomEvent("next-autocomplete:result-click", {
        bubbles: true,
        detail: {
          eventName: this.eventNameValue,
          fieldName: this.fieldNameValue,
          position,
          inputText,
          ...linkData,
        },
      }),
    )
  }

  #loadResults(query: string) {
    const nextUrl = new URL(this.endpointUrlValue, window.location.origin)
    nextUrl.searchParams.set("q", query)
    nextUrl.searchParams.set("turbo_frame_id", this.turboFrameIdValue)
    nextUrl.searchParams.set("limit", this.limitValue)
    this.resultsTarget.setAttribute("src", nextUrl.toString())
    this.#showListbox()
  }

  // Keyboard handling follows W3C APG "combobox-autocomplete-list":
  // https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-list/
  //
  // Important invariants:
  // - DOM focus stays on the textbox at all times while the listbox is open.
  //   "Focused" option is conveyed only via `aria-activedescendant` and
  //   `aria-selected` — we never call `link.focus()` or `option.focus()`.
  // - `Home`/`End` are left to the browser so they act on the textbox caret.
  // - Arrow navigation does NOT wrap (last → first or first → last).
  // - First Down/Up press on a closed listbox only opens it; a second press
  //   moves visual focus into the listbox.
  navigate(event: KeyboardEvent) {
    const key = event.key

    if (key === "Tab") {
      this.#hideListbox()
      return
    }

    switch (key) {
      case "ArrowDown":
        event.preventDefault()
        // Alt+Down (and a plain Down on a closed listbox): open the listbox
        // WITHOUT moving visual focus — APG explicitly forbids advancing.
        if (event.altKey || this.resultsTarget.hidden) {
          this.#showListbox()
          return
        }
        this.#moveFocus(1)
        break

      case "ArrowUp":
        event.preventDefault()
        if (event.altKey) {
          // Alt + Up Arrow: close the listbox without changing the value.
          this.#hideListbox()
          return
        }
        if (this.resultsTarget.hidden) {
          // Up on a closed listbox opens it without moving visual focus.
          this.#showListbox()
          return
        }
        this.#moveFocus(-1)
        break

      case "Enter":
        event.preventDefault()
        this.commitSelection()
        break

      case "Escape":
        event.preventDefault()
        this.#escapeAction()
        break

      // Home / End intentionally not handled: APG says they move the caret
      // in the textbox, which is the browser default. Intercepting would
      // break users navigating long queries.
    }
  }

  optionTargetConnected() {
    this.#refreshOptions()
  }

  #refreshOptions() {
    this.currentIndex = -1
  }

  #getLinkFromOption(option: HTMLElement): HTMLAnchorElement | null {
    return option.querySelector("a")
  }

  #moveFocus(direction: number) {
    if (this.optionTargets.length === 0) {
      return
    }

    // No wrap — APG says Down does nothing on the last option and Up does
    // nothing on the first. From `currentIndex = -1` (no option focused yet)
    // a Down jumps to 0 and Up jumps to the last option.
    let newIndex: number
    if (this.currentIndex === -1) {
      newIndex = direction > 0 ? 0 : this.optionTargets.length - 1
    } else {
      newIndex = this.currentIndex + direction
    }

    if (newIndex < 0 || newIndex >= this.optionTargets.length) {
      return
    }

    this.#setVisualFocus(newIndex)
  }

  // Visual focus only — DOM focus stays on the textbox. The selected option
  // is conveyed by `aria-activedescendant` on the input and `aria-selected`
  // on the option, per APG combobox-autocomplete-list.
  #setVisualFocus(index: number) {
    if (index < 0 || index >= this.optionTargets.length) {
      return
    }

    this.currentIndex = index
    const currentOption = this.optionTargets[this.currentIndex]

    this.#removeSelection()
    currentOption.setAttribute("aria-selected", "true")
    this.inputTarget.setAttribute("aria-activedescendant", currentOption.id || "")
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

    // When `display_value` is True the visible input itself carries the form
    // value and there is no hidden sibling — see input.html.
    if (this.hasHiddenInputTarget) {
      this.hiddenInputTarget.value = value
    }
    this.inputTarget.value = selectedValue
    // Clear the typing flag so a subsequent refocus does not re-open the
    // listbox with the same suggestions the user just picked.
    this.#userIsTyping = false
    this.#hideListbox()

    const commitEvent = new CustomEvent("next-autocomplete:commit", {
      bubbles: true,
      detail: { option: selected, value, selectedValue },
    })
    this.element.dispatchEvent(commitEvent)

    // Analytics: fire result-click event if eventName is configured
    if (this.eventNameValue) {
      const position = this.optionTargets.indexOf(selected) + 1
      this.element.dispatchEvent(
        new CustomEvent("next-autocomplete:result-click", {
          bubbles: true,
          detail: {
            eventName: this.eventNameValue,
            fieldName: this.fieldNameValue,
            position,
            inputText: this.inputTarget.value,
            selectedValue,
          },
        }),
      )
    }
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
    this.#positionListbox()
  }

  // Position the (position:fixed) listbox under the autocomplete widget and
  // clamp its height so its bottom edge stays above the bottom of the
  // document body by LISTBOX_BOTTOM_MARGIN_PX. The body bottom matches the
  // iframe bottom when embedded, so the dropdown never spills outside the
  // iframe.
  //
  // Width/left come from `this.element` (the controller wrapper) rather than
  // `this.inputTarget` because the visual search box can be wider than the
  // raw <input> on the homepage variant — it includes a search icon and
  // padding. Top still comes from the input bottom: that is where the user
  // expects the dropdown to start.
  #positionListbox() {
    if (this.resultsTarget.hidden) return

    const inputRect = this.inputTarget.getBoundingClientRect()
    const wrapperRect = this.element.getBoundingClientRect()
    this.resultsTarget.style.top = `${inputRect.bottom}px`
    this.resultsTarget.style.left = `${wrapperRect.left}px`
    this.resultsTarget.style.width = `${wrapperRect.width}px`
    // Clear any previous max-height before measuring, otherwise a clamped
    // value from a prior pass leaks into the new layout.
    this.resultsTarget.style.maxHeight = ""

    // Read the actual top *after* layout. Tailwind margin classes (e.g.
    // qf-mt-1w on the homepage variant) shift the box below inputRect.bottom
    // and we want to respect that visual gap in the clamp.
    const frameTop = this.resultsTarget.getBoundingClientRect().top
    const margin = AutocompleteController.#LISTBOX_BOTTOM_MARGIN_PX
    const bodyBottom = document.documentElement.clientHeight
    const available = computeAvailableHeight(frameTop, bodyBottom, margin)
    this.resultsTarget.style.maxHeight = `${available}px`
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
