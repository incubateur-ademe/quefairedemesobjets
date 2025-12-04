import { WindowResizeController } from "stimulus-use"

import PinpointController from "./pinpoint_controller"

class ActeurController extends WindowResizeController {
  static targets = ["handle", "actions", "content"]
  static values = { mapContainerId: String, draggable: Boolean }
  isDragging = false
  panelHeight: number
  startY: number
  currentTranslateY: number
  hidden = true
  startTranslateY = 0
  initialTranslateY = 200
  initialTransition = "transform ease 0.5s"
  // snapPoints defines the area in percentage of the parent where the
  // panel will adhere with magnetism.
  // When the user drags the panel close to a snapPoint, the panel will
  // stop at this point. This allows to control the panel's position precisely
  // 0 = fully open, 1 = fully closed
  snapPoints = [0.3, 0.5, 0.8, 1]

  declare readonly mapContainerIdValue: string
  declare readonly draggableValue: boolean
  declare readonly handleTarget: HTMLElement
  declare readonly contentTarget: HTMLElement
  declare readonly actionsTarget: HTMLElement
  declare readonly hasActionsTarget: Function

  initialize() {
    if (this.draggableValue) {
      this.element.addEventListener("mousedown", this.#dragStart.bind(this))
      this.handleTarget.addEventListener("touchstart", this.#dragStart.bind(this))

      this.element.addEventListener("mousemove", this.#dragMove.bind(this))
      this.element.addEventListener("touchmove", this.#dragMove.bind(this))

      window.addEventListener("mouseup", this.#dragEnd.bind(this))
      window.addEventListener("touchend", this.#dragEnd.bind(this))
    }

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

  #computePanelTranslateY(): number {
    const matrix = window.getComputedStyle(this.element).transform

    if (matrix !== "none") {
      return Math.abs(parseFloat(matrix.split(",")[5]))
    }

    return this.initialTranslateY
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

  #dragStart(event: TouchEvent) {
    this.isDragging = true
    const eventY = event?.y || event?.touches[0].clientY
    this.startY = Math.abs(eventY)
    this.startTranslateY = this.#computePanelTranslateY()
    this.element.style.transition = ""
  }

  #setTranslateY(value: number) {
    if (!this.draggableValue) {
      return
    }

    if (window.matchMedia("screen and (max-width:768px)").matches) {
      let nextValue = value
      if (Math.abs(value) < this.initialTranslateY) {
        nextValue = -1 * this.initialTranslateY
      }

      this.element.style.transform = `translateY(${nextValue}px)`
    }
    this.#resizeContent()
  }

  #dragMove(event: MouseEvent | TouchEvent) {
    if (!this.isDragging) return

    // Prevent text selection the element being moved
    event.preventDefault()
    this.element.classList.add("qf-select-none")

    const eventY = event?.y || event?.touches[0].clientY
    const pixelsDragged = this.startY - eventY
    const pixelsDraggedOffsetted = pixelsDragged + this.startTranslateY

    this.currentTranslateY = Math.min(pixelsDraggedOffsetted, this.panelHeight)
    this.#setTranslateY(-1 * this.currentTranslateY)
  }

  #resetTransition() {
    if (window.matchMedia("screen and (max-width:768px)").matches) {
      this.element.style.transition = this.initialTransition
    }
  }

  #dragEnd(event: MouseEvent | TouchEvent) {
    if (!this.isDragging) return
    this.isDragging = false
    this.#resetTransition()
    this.element.classList.remove("qf-select-none")

    const currentDragRatio = this.currentTranslateY / this.panelHeight

    // Find closest snap point
    let closestSnapPoint = this.snapPoints[0]
    let minDiff = Math.abs(currentDragRatio - closestSnapPoint)
    for (const snapPoint of this.snapPoints) {
      const diff = Math.abs(currentDragRatio - snapPoint)
      if (diff < minDiff) {
        minDiff = diff
        closestSnapPoint = snapPoint
      }
    }

    // Snap to the closest point
    const snapY = -1 * closestSnapPoint * this.panelHeight
    this.#setTranslateY(snapY)

    this.element.addEventListener("transitionend", this.#resizeContent.bind(this), {
      once: true,
    })
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
