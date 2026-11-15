import PinpointController from "./pinpoint_controller"
import { Controller } from "@hotwired/stimulus"

const TABBABLE_SELECTOR =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select, textarea, summary, [tabindex]:not([tabindex="-1"])'

class ActeurController extends Controller<HTMLDialogElement> {
  static targets = ["content"]
  static values = { mapContainerId: String, modal: Boolean }

  declare readonly mapContainerIdValue: string
  declare readonly modalValue: boolean
  declare readonly contentTarget: HTMLElement

  #show() {
    // Reset scroll when jumping from a acteur detail to another.
    this.element.scrollTo(0, 0)
    if (!this.element.open) {
      // The map stays usable next to the panel; the list does not.
      if (this.modalValue) {
        this.element.showModal()
      } else {
        this.element.show()
      }
    }
    // Move keyboard focus into the panel when it opens
    const closeButton = this.element.querySelector<HTMLElement>(
      "[data-testid='acteur-details-close']",
    )
    if (closeButton) {
      closeButton.focus()
    } else {
      this.element.focus()
    }
  }

  hide() {
    this.element.close()
    PinpointController.clearActivePinpoints()
  }

  // Keeps Tab and Shift+Tab looping inside the modal panel.
  trapFocus(event: KeyboardEvent) {
    if (event.key !== "Tab" || !this.modalValue) return
    const tabbables = [
      ...this.element.querySelectorAll<HTMLElement>(TABBABLE_SELECTOR),
    ].filter(
      (element) =>
        element.checkVisibility({ checkVisibilityCSS: true }) && element.tabIndex >= 0,
    )
    const first = tabbables[0]
    const last = tabbables[tabbables.length - 1]
    if (!first) return

    const isLeavingBackwards = event.shiftKey && document.activeElement === first
    const isLeavingForwards = !event.shiftKey && document.activeElement === last
    if (isLeavingBackwards || isLeavingForwards) {
      event.preventDefault()
      ;(isLeavingBackwards ? last : first).focus()
    }
  }

  #showPanelWhenTurboFrameLoad(event: CustomEvent) {
    // TODO : fetch this variable from template, using turbo_tags.acteur_frame_id
    let acteurDetailTurboFrameId = `${this.mapContainerIdValue}:acteur-detail`

    if (event.target.id === acteurDetailTurboFrameId) {
      this.#show()
      this.#dispatchActeurViewed(event.target as HTMLElement)
    }
  }

  #dispatchActeurViewed(frame: HTMLElement) {
    const article = frame.querySelector<HTMLElement>("article[data-acteur-uuid]")
    if (!article) return
    this.element.dispatchEvent(
      new CustomEvent("acteur-details:viewed", {
        bubbles: true,
        detail: {
          acteurUuid: article.dataset.acteurUuid,
          acteurType: article.dataset.acteurType,
          sources: article.dataset.acteurSources?.split(",").filter(Boolean) ?? [],
        },
      }),
    )
  }

  connect() {
    document.addEventListener(
      "turbo:frame-load",
      this.#showPanelWhenTurboFrameLoad.bind(this),
    )
  }
}

export default ActeurController
