import { Controller } from "@hotwired/stimulus"
import { useClickOutside, useDebounce } from "stimulus-use"

const TYPING_DELAY_MS = 150

/**
 * A suggestion. Only `label` is mandatory: the remaining fields depend on the
 * endpoint (a slug for an objet, coordinates for an address) and travel as is
 * in the `chosen` event.
 */
type Suggestion = {
  label: string
  detail?: string
  [key: string]: unknown
}

/**
 * Autocomplete combobox (W3C APG combobox-autocomplete-list).
 *
 * Serves both header fields, objet and address: only the queried URL and the
 * shape of the suggestions change, not the keyboard behavior nor the ARIA.
 *
 * The list only opens once something is typed, never on focus: the MVP
 * (#3295) explicitly rules out a list open from the start.
 */
export default class extends Controller<HTMLElement> {
  static targets = ["input", "list", "status", "hidden"]
  static values = {
    url: String,
    minLength: { type: Number, default: 2 },
  }

  declare readonly inputTarget: HTMLInputElement
  declare readonly listTarget: HTMLElement
  declare readonly statusTarget: HTMLElement
  declare readonly hasStatusTarget: boolean
  /** Hidden fields filled on choice, so that the form submits them. */
  declare readonly hiddenTargets: HTMLInputElement[]
  declare urlValue: string
  declare minLengthValue: number

  static debounces = [{ name: "search", wait: TYPING_DELAY_MS }]

  private pendingRequest: AbortController | null = null
  private suggestions: Suggestion[] = []
  private active = -1

  connect() {
    useDebounce(this)
    useClickOutside(this)
  }

  disconnect() {
    this.pendingRequest?.abort()
  }

  clickOutside() {
    this.#close()
  }

  async search() {
    const query = this.inputTarget.value.trim()
    // Any keystroke invalidates the previous choice: otherwise, editing the
    // text without choosing again would submit the previous address's
    // coordinates.
    this.#clearHidden()

    if (query.length < this.minLengthValue) return this.#close()

    this.pendingRequest?.abort()
    this.pendingRequest = new AbortController()

    try {
      const response = await fetch(`${this.urlValue}?q=${encodeURIComponent(query)}`, {
        signal: this.pendingRequest.signal,
      })
      if (!response.ok) throw new Error(`response ${response.status}`)
      const { results } = await response.json()
      this.suggestions = results
      this.#render()
    } catch (error) {
      if ((error as Error).name === "AbortError") return
      this.#close()
    }
  }

  navigate(event: KeyboardEvent) {
    if (!this.suggestions.length) return

    const keys: Record<string, () => void> = {
      ArrowDown: () => this.#activate(this.active + 1),
      ArrowUp: () => this.#activate(this.active - 1),
      Enter: () => this.#choose(this.active),
      Escape: () => this.#close(),
    }
    const action = keys[event.key]
    if (!action) return

    event.preventDefault()
    action()
  }

  chooseFromClick(event: MouseEvent) {
    const option = (event.target as HTMLElement).closest("[data-index]")
    if (option) this.#choose(Number((option as HTMLElement).dataset.index))
  }

  #activate(index: number) {
    const total = this.suggestions.length
    this.active = ((index % total) + total) % total
    this.#render()
  }

  #choose(index: number) {
    const suggestion = this.suggestions[index]
    if (!suggestion) return

    this.inputTarget.value = suggestion.label
    this.#fillHidden(suggestion)
    this.dispatch("chosen", { detail: suggestion })
    this.#close()
  }

  /**
   * Copies the suggestion into the hidden fields, by `data-key`.
   *
   * This is how the longitude, the latitude and the precise nature of an
   * address reach the server: the user does not type them, but the map needs
   * them.
   */
  #fillHidden(suggestion: Suggestion) {
    for (const field of this.hiddenTargets) {
      const value = suggestion[field.dataset.key ?? ""]
      field.value = value === undefined || value === null ? "" : String(value)
    }
  }

  #clearHidden() {
    for (const field of this.hiddenTargets) field.value = ""
  }

  #render() {
    this.listTarget.innerHTML = this.suggestions
      .map((suggestion, index) => {
        const detail = suggestion.detail
          ? ` <span class="qfa-combobox__detail">${escape(suggestion.detail)}</span>`
          : ""
        return (
          `<li role="option" data-index="${index}" id="${this.#optionId(index)}"` +
          ` aria-selected="${index === this.active}"` +
          ` class="qfa-combobox__option">${escape(suggestion.label)}${detail}</li>`
        )
      })
      .join("")

    this.listTarget.hidden = false
    this.inputTarget.setAttribute("aria-expanded", "true")
    this.inputTarget.setAttribute(
      "aria-activedescendant",
      this.active >= 0 ? this.#optionId(this.active) : "",
    )
    this.#announce(
      this.suggestions.length
        ? `${this.suggestions.length} suggestion${this.suggestions.length > 1 ? "s" : ""}`
        : "Aucune suggestion",
    )
  }

  #close() {
    this.listTarget.hidden = true
    this.listTarget.innerHTML = ""
    this.suggestions = []
    this.active = -1
    this.inputTarget.setAttribute("aria-expanded", "false")
    this.inputTarget.removeAttribute("aria-activedescendant")
  }

  #optionId(index: number): string {
    return `${this.element.id || "combobox"}-option-${index}`
  }

  #announce(message: string) {
    if (this.hasStatusTarget) this.statusTarget.textContent = message
  }
}

/** Labels come from a third-party API: they are not trusted HTML. */
function escape(text: string): string {
  const node = document.createElement("span")
  node.textContent = text
  return node.innerHTML
}
