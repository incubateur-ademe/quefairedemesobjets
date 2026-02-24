import { WindowResizeController } from "stimulus-use"

import PinpointController from "./pinpoint_controller"

class ActeurController extends WindowResizeController {
  static targets = ["content"]
  static values = { mapContainerId: String }

  declare readonly mapContainerIdValue: string
  declare readonly contentTarget: HTMLElement

  windowResize({ width, height, event }) {
    this.contentTarget.style.maxHeight = ``
    this.#resizeContent()
  }

  #show() {
    // Reset scroll when jumping from a acteur detail to another.
    this.element.scrollTo(0, 0)
    if (this.element.ariaHidden !== "false") {
      this.element.ariaHidden = "false"
    }

    this.element.dataset.exitAnimationEnded = "false"
    this.#resizeContent()
  }

  hide() {
    this.element.ariaExpanded = "false"
    this.element.ariaHidden = "true"
    this.element.addEventListener(
      "animationend",
      () => {
        this.element.dataset.exitAnimationEnded = "true"
      },
      { once: true },
    )
    PinpointController.clearActivePinpoints()
  }

  #showPanelWhenTurboFrameLoad(event) {
    // TODO : fetch this variable from template, using turbo_tags.acteur_frame_id
    let acteurDetailTurboFrameId = `${this.mapContainerIdValue}:acteur-detail`

    if (event.target.id === acteurDetailTurboFrameId) {
      this.#show()
    }
  }

  connect() {
    document.addEventListener(
      "turbo:frame-load",
      this.#showPanelWhenTurboFrameLoad.bind(this),
    )
  }

  #resizeContent() {
    const mapContainer = this.element.parentElement!
    const elementsAboveContentHeight = Math.abs(
      mapContainer.getBoundingClientRect().top -
        this.contentTarget.getBoundingClientRect().top,
    )
    const currentPanelHeight = mapContainer.offsetHeight
    const nextContentHeight = currentPanelHeight - elementsAboveContentHeight

    this.contentTarget.style.maxHeight = `${nextContentHeight}px`
  }
}

export default ActeurController
