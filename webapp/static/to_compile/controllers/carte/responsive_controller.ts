import { Controller } from "@hotwired/stimulus"

/**
 * Responsive Controller
 *
 * Moves element content based on media query matching.
 *
 * Without a `target`: content is moved to a hidden wrapper at the end of
 * <body> when the query does NOT match (legacy behaviour — hides content
 * on larger screens).
 *
 * With a `target` selector: content is moved TO the target element when
 * the query MATCHES, and restored to its original position when the query
 * no longer matches. Useful for moving content out of a modal on desktop.
 *
 * With `closeModal`: when content is moved to the target, the closest
 * ancestor `<dialog class="fr-modal">` is closed via the DSFR modal API.
 *
 * Usage with target:
 * <div data-controller="responsive"
 *      data-responsive-media-query-value="(min-width: 768px)"
 *      data-responsive-target-value="#desktop-container"
 *      data-responsive-close-modal-value="true">
 *   Content (starts here on mobile, moves to #desktop-container on desktop)
 * </div>
 */
export default class extends Controller {
  static values = {
    mediaQuery: String,
    target: { type: String, default: "" },
    closeModal: { type: Boolean, default: false },
  }

  declare mediaQueryValue: string
  declare targetValue: string
  declare closeModalValue: boolean

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

    if (this.targetValue) {
      // Target mode: move to target on match, restore on !match
      if (this.#mediaQueryList.matches) {
        this.#moveToTarget()
      } else {
        this.#restoreFromTarget()
      }
    } else {
      // Legacy mode: restore on match, hide on !match
      if (this.#mediaQueryList.matches) {
        this.#restoreFromLegacyWrapper()
      } else {
        this.#moveToLegacyWrapper()
      }
    }
  }

  // ── Target mode ──────────────────────────────────────────────

  #moveToTarget() {
    const targetEl = this.#resolveTarget()
    if (!targetEl || this.element.children.length === 0) return

    // Don't move if content is already in the target
    if (targetEl.contains(this.element.firstChild)) return

    while (this.element.firstChild) {
      targetEl.appendChild(this.element.firstChild)
    }

    if (this.closeModalValue) {
      this.#closeParentModal()
    }
  }

  #restoreFromTarget() {
    const targetEl = this.#resolveTarget()
    if (!targetEl || targetEl.children.length === 0) return

    // Don't move if content is already back in the original element
    if (this.element.contains(targetEl.firstChild)) return

    while (targetEl.firstChild) {
      this.element.appendChild(targetEl.firstChild)
    }
  }

  #resolveTarget(): HTMLElement | null {
    return document.querySelector(this.targetValue)
  }

  #closeParentModal() {
    const dialog = this.element.closest<HTMLDialogElement>("dialog.fr-modal")
    if (!dialog) return

    // Use DSFR API if available; otherwise native dialog.close()
    const dsfr = (window as Record<string, unknown>).dsfr as
      | ((el: Element) => { modal: { conceal: () => void } })
      | undefined
    if (dsfr) {
      dsfr(dialog).modal.conceal()
    } else {
      dialog.close()
    }
  }

  // ── Legacy mode (body-end hidden wrapper) ────────────────────

  #moveToLegacyWrapper() {
    const wrapper = this.#getOrCreateLegacyWrapper()
    if (this.element.children.length === 0) return
    if (wrapper.contains(this.element.firstChild)) return

    while (this.element.firstChild) {
      wrapper.appendChild(this.element.firstChild)
    }
  }

  #restoreFromLegacyWrapper() {
    const wrapper = this.#getOrCreateLegacyWrapper()
    if (wrapper.children.length === 0) return
    if (this.element.contains(wrapper.firstChild)) return

    while (wrapper.firstChild) {
      this.element.appendChild(wrapper.firstChild)
    }
  }

  #restoreToOriginalPosition() {
    if (this.targetValue) {
      this.#restoreFromTarget()
    } else {
      this.#restoreFromLegacyWrapper()
    }
  }

  #getOrCreateLegacyWrapper(): HTMLElement {
    let wrapper = document.getElementById(this.#wrapperId)
    if (!wrapper) {
      wrapper = document.createElement("div")
      wrapper.id = this.#wrapperId
      wrapper.setAttribute("hidden", "")
      document.body.appendChild(wrapper)
    }
    return wrapper
  }
}
