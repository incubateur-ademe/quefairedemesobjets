import { Controller } from "@hotwired/stimulus"
import { clearActivePinpoints, removeHash } from "../../js/helpers"

class ActeurController extends Controller<HTMLElement> {
  static targets = ["content", "frame"]
  isDragging = false
  panelHeight: number
  startY: number
  currentTranslateY: number
  hidden = true
  startTranslateY = 0
  initialTranslateY = 140
  initialTransition = 'transform ease 0.5s';
  // snapPoints defines the area in percentage of the parent where the
  // panel will adhere with magnetism.
  // When the user drags the panel close to a snapPoint, the panel will
  // stop at this point. This allows to control the panel's position precisely
  // 0 = fully open, 1 = fully closed
  snapPoints = [0.2, 0.5, 0.8];

  declare readonly contentTarget: HTMLElement
  declare readonly frameTarget: HTMLElement

  initialize() {
    this.element.style.transition = this.initialTransition;
    this.#setTranslateY(0)
    // this.element.style.height = `calc(100svh - 20%)`
    this.element.addEventListener("mousedown", this.#dragStart.bind(this))
    this.element.addEventListener('touchstart', this.#dragStart.bind(this));

    this.element.addEventListener('mousemove', this.#dragMove.bind(this));
    this.element.addEventListener('touchmove', this.#dragMove.bind(this));

    window.addEventListener('mouseup', this.#dragEnd.bind(this));
    window.addEventListener('touchend', this.#dragEnd.bind(this));
  }

  #computePanelTranslateY(): number {
    const matrix = window.getComputedStyle(this.element).transform;

    if (matrix !== 'none') {
      return Math.abs(parseFloat(matrix.split(',')[5]));
    }

    return this.initialTranslateY
  }

  #show() {
    this.element.style.transition = this.initialTransition;
    if (this.element.ariaHidden !== "false") {
      this.element.ariaHidden = "false"
    }

    this.element.dataset.exitAnimationEnded = "false"
    this.panelHeight = this.element.offsetHeight

    if (window.matchMedia('screen and (max-width:768px)').matches) {
      this.element.scrollIntoView()

      if (this.hidden) {
        this.#setTranslateY(-1 * this.initialTranslateY)
      } else {
        this.hidden = false
      }
    }
  }

  hide() {
    removeHash()
    this.element.ariaExpanded = "false"
    this.element.ariaHidden = "true"
    this.element.addEventListener(
      "animationend",
      () => {
        this.element.dataset.exitAnimationEnded = "true"
      },
      { once: true },
    )
    clearActivePinpoints()
    this.#setTranslateY(-1 * this.initialTranslateY)
    this.hidden = true
  }

  #showHidePanelWhenTurboFrameLoad(event) {
    if (event.target.id === "acteur-detail") {
      this.#show()
    } else {
      this.hide()
    }
  }

  connect() {
    // Prevents the leaflet map to move when the user moves panel
    this.element.addEventListener("touchmove", (event) =>
      event.stopPropagation(),
    )
    document.addEventListener("turbo:frame-load", this.#showHidePanelWhenTurboFrameLoad.bind(this))
  }

  #dragStart(event: TouchEvent) {
    this.isDragging = true;
    const eventY = event?.y || event?.touches[0].clientY
    this.startY = Math.abs(eventY)
    this.startTranslateY = this.#computePanelTranslateY()
    this.element.style.transition = 'none';
  }

  #setTranslateY(value: number) {
    if (window.matchMedia('screen and (max-width:768px)').matches) {
      let nextValue = value
      if (Math.abs(value) < this.initialTranslateY) {
        nextValue = -1 * this.initialTranslateY
      }

      this.element.style.transform = `translateY(${nextValue}px)`;
    }
  }

  #dragMove(event: MouseEvent | TouchEvent) {
    if (!this.isDragging) return;

    // Prevent text selection the element being moved
    event.preventDefault()
    this.element.classList.add("qf-select-none")

    const eventY = event?.y || event?.touches[0].clientY
    const pixelsDragged = this.startY - eventY
    const pixelsDraggedOffsetted = pixelsDragged + this.startTranslateY

    this.currentTranslateY = Math.min(pixelsDraggedOffsetted, this.panelHeight)
    this.#setTranslateY(-1 * this.currentTranslateY);
  }

  #dragEnd(event: MouseEvent | TouchEvent) {
    if (!this.isDragging) return;
    this.isDragging = false;
    this.element.style.transition = this.initialTransition;
    this.element.classList.remove("qf-select-none")

    // Current drag ratio
    const ratio = this.currentTranslateY / this.panelHeight;

    // Find closest snap point
    let closest = this.snapPoints[0];
    let minDiff = Math.abs(ratio - closest);
    for (const point of this.snapPoints) {
      const diff = Math.abs(ratio - point);
      if (diff < minDiff) {
        minDiff = diff;
        closest = point;
      }
    }

    // Snap to the closest point
    const snapY = -1 * closest * this.panelHeight;
    this.#setTranslateY(snapY);
    this.#resizeContent()
    window.dispatchEvent(new Event("resize"))
  }

  #resizeContent() {
    const mapContainer  = this.element.parentElement!
    const elementsAboveContentHeight = Math.abs(mapContainer.getBoundingClientRect().y - this.contentTarget.getBoundingClientRect().y)
    const currentPanelHeight = mapContainer.offsetHeight
    const nextContentHeight = currentPanelHeight - elementsAboveContentHeight - 50

    console.log({ nextContentHeight, currentPanelHeight, elementsAboveContentHeight, })

    this.contentTarget.style.maxHeight = `${nextContentHeight}px`
  }
}

export default ActeurController
