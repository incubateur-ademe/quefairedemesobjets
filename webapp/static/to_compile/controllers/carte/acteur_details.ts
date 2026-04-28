import PinpointController from "./pinpoint_controller"
import { Controller } from "@hotwired/stimulus"

class ActeurController extends Controller {
  static targets = ["content"]
  static values = { mapContainerId: String }

  declare readonly mapContainerIdValue: string
  declare readonly contentTarget: HTMLElement

  #show() {
    // Reset scroll when jumping from a acteur detail to another.
    this.element.scrollTo(0, 0)
    if (this.element.ariaHidden !== "false") {
      this.element.ariaHidden = "false"
    }
  }

  hide() {
    this.element.ariaExpanded = "false"
    this.element.ariaHidden = "true"
    PinpointController.clearActivePinpoints()
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
