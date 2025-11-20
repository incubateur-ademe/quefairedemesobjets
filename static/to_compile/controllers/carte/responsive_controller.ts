import { Controller } from "@hotwired/stimulus"

/**
 * Responsive Controller
 *
 * Moves element content to a hidden wrapper at the end of body when media query matches,
 * and restores content to original position when media query no longer matches.
 *
 * Usage:
 * <div data-controller="responsive" data-responsive-media-query-value="(max-width: 768px)">
 *   Content to be moved
 * </div>
 */
export default class extends Controller {
  static values = {
    mediaQuery: String,
  }

  declare mediaQueryValue: string

  #mediaQueryList: MediaQueryList | null = null
  #boundHandleMediaChange: (() => void) | null = null

  // Note: crypto.randomUUID() requires a secure context (HTTPS or localhost)
  // This will throw an error in non-secure contexts (HTTP)
  #wrapperId: string = `responsive-wrapper-${crypto.randomUUID()}`

  connect() {
    if (!this.mediaQueryValue) {
      console.warn("ResponsiveController: no media query provided")
      return
    }

    this.#mediaQueryList = window.matchMedia(this.mediaQueryValue)
    this.#boundHandleMediaChange = this.#handleMediaChange.bind(this)
    this.#mediaQueryList.addEventListener("change", this.#boundHandleMediaChange)
    this.#handleMediaChange()
  }

  disconnect() {
    if (this.#mediaQueryList && this.#boundHandleMediaChange) {
      this.#mediaQueryList.removeEventListener("change", this.#boundHandleMediaChange)
    }
    this.#restoreToOriginalPosition()
  }

  #handleMediaChange() {
    if (!this.#mediaQueryList) return

    if (this.#mediaQueryList.matches) {
      this.#restoreToOriginalPosition()
    } else {
      this.#moveToBodyEnd()
    }
  }

  #moveToBodyEnd() {
    if (document.getElementById(this.#wrapperId)) {
      return
    }

    const wrapper = document.createElement("div")
    wrapper.id = this.#wrapperId
    wrapper.setAttribute("hidden", "")

    while (this.element.firstChild) {
      wrapper.appendChild(this.element.firstChild)
    }

    document.body.appendChild(wrapper)
  }

  #restoreToOriginalPosition() {
    const wrapper = document.getElementById(this.#wrapperId)
    if (!wrapper) {
      return
    }

    while (wrapper.firstChild) {
      this.element.appendChild(wrapper.firstChild)
    }

    wrapper.remove()
  }
}
