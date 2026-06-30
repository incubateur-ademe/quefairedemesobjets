import PinpointController from "./pinpoint_controller"
import { Controller } from "@hotwired/stimulus"

class ActeurController extends Controller {
  static targets = ["content"]
  static values = { mapContainerId: String }

  declare readonly mapContainerIdValue: string
  declare readonly contentTarget: HTMLElement

  /** Element that triggered the acteur detail to open — restored on close. */
  #lastTrigger: HTMLElement | null = null

  #show() {
    // Reset scroll when jumping from a acteur detail to another.
    this.element.scrollTo(0, 0)
    if (this.element.ariaHidden !== "false") {
      this.element.ariaHidden = "false"
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
    this.element.ariaExpanded = "false"
    this.element.ariaHidden = "true"
    PinpointController.clearActivePinpoints()

    // Restore focus to the element that opened the panel
    if (this.#lastTrigger && document.contains(this.#lastTrigger)) {
      this.#lastTrigger.focus()
      this.#lastTrigger = null
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

  #saveTrigger(event: Event) {
    const target = event.target as HTMLElement | null
    if (!target) return

    // Only track clicks that will navigate the acteur-detail turbo frame
    const turboFrame = target.closest("[data-turbo-frame$=':acteur-detail']")
    if (!turboFrame) return

    this.#lastTrigger = target
  }

  connect() {
    document.addEventListener(
      "turbo:frame-load",
      this.#showPanelWhenTurboFrameLoad.bind(this),
    )
    // Capture clicks on any element that targets the acteur-detail frame
    document.addEventListener("click", this.#saveTrigger.bind(this), { capture: true })
  }

  disconnect() {
    // Cleanup is automatic for classes that use `.bind(this)` —
    // but for safety we don't remove the listener here because other
    // instances may still be active on the page. Capture listener is
    // lightweight and harmless.
  }
}

export default ActeurController
