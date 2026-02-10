import { WindowResizeController } from "stimulus-use"

import PinpointController from "./pinpoint_controller"

class ActeurController extends WindowResizeController {
  static targets = ["actions", "content"]
  static values = { mapContainerId: String }
  panelHeight: number
  hidden = true
  initialTranslateY = 200
  initialTransition = "transform ease 0.5s"

  declare readonly mapContainerIdValue: string
  declare readonly contentTarget: HTMLElement
  declare readonly actionsTarget: HTMLElement
  declare readonly hasActionsTarget: Function

  initialize() {
    if (this.hasActionsTarget) {
      this.initialTranslateY = 20 + this.actionsTarget.getBoundingClientRect().bottom
    }
  }

  windowResize({ width, height, event }) {
    this.element.style.transition = ""
    this.element.style.transform = ``
    this.contentTarget.style.maxHeight = ``
    this.#setTranslateY()
  }

  #show() {
    this.#resetTransition()

    // Reset scroll when jumping from a acteur detail to another.
    this.element.scrollTo(0, 0)
    if (this.element.ariaHidden !== "false") {
      this.element.ariaHidden = "false"
    }

    this.element.dataset.exitAnimationEnded = "false"
    this.panelHeight = this.element.offsetHeight

    if (window.matchMedia("screen and (max-width:768px)").matches) {
      if (this.hidden) {
        this.#setTranslateY(-1 * this.initialTranslateY)
      } else {
        this.hidden = false
      }
    }

    this.element.addEventListener("transitionend", () => {
      if (window.innerWidth > 768) {
        return
      }

      if (this.element.parentElement?.getBoundingClientRect().bottom > window.scrollY) {
        this.element.parentElement!.scrollIntoView({
          block: "end",
          behavior: "smooth",
        })
      }
    })
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
    this.#setTranslateY(-1 * this.initialTranslateY)
    this.hidden = true
  }

  #showPanelWhenTurboFrameLoad(event) {
    // TODO : fetch this variable from template, using turbo_tags.acteur_frame_id
    let acteurDetailTurboFrameId = `${this.mapContainerIdValue}:acteur-detail`

    if (event.target.id === acteurDetailTurboFrameId) {
      this.#show()
    }
  }

  connect() {
    // Prevents the map to move when the user moves panel
    this.element.addEventListener("touchmove", (event) => event.stopPropagation())
    document.addEventListener(
      "turbo:frame-load",
      this.#showPanelWhenTurboFrameLoad.bind(this),
    )
  }

  #setTranslateY(value: number) {
    if (window.matchMedia("screen and (max-width:768px)").matches) {
      let nextValue = value
      if (Math.abs(value) < this.initialTranslateY) {
        nextValue = -1 * this.initialTranslateY
      }

      this.element.style.transform = `translateY(${nextValue}px)`
    }
    this.#resizeContent()
  }

  #resetTransition() {
    if (window.matchMedia("screen and (max-width:768px)").matches) {
      this.element.style.transition = this.initialTransition
    }
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
