import { Controller } from "@hotwired/stimulus"
import { clearActivePinpoints, removeHash } from "../../js/helpers"

class ActeurController extends Controller<HTMLElement> {
  isDragging = false
  panelHeight: number
  startY: number
  currentTranslateY: number
  startTranslateY = 0
  initialTranslateY: number
  initialTransition: string
  declare readonly frameTarget: HTMLElement

  initialize() {
    this.initialTranslateY = this.#computePanelTranslateY()
    this.initialTransition = window.getComputedStyle(this.element).transition

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

    // TODO: remove hardcoded value
    return 140
  }

  #show() {
    if (this.element.ariaHidden !== "false") {
      this.element.ariaHidden = "false"
    }

    this.element.dataset.exitAnimationEnded = "false"

    if (window.matchMedia('screen and (max-width:768px)').matches) {
      this.element.scrollIntoView()
    }

    this.panelHeight = this.element.offsetHeight
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
    console.log("HIDE", this)
    this.#setTranslateY(-1 * this.initialTranslateY)
  }

  refreshPanelOnNavigation(event) {
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
    document.addEventListener("turbo:frame-load", this.refreshPanelOnNavigation.bind(this))
  }

  #dragStart(event: TouchEvent) {
    // event.preventDefault()
    this.isDragging = true;
    const eventY = event?.y || event?.touches[0].clientY
    console.log({ eventY, event })
    this.startY = Math.abs(eventY)
    this.startTranslateY = this.#computePanelTranslateY()
    this.element.style.transition = 'none';
  }

  #setTranslateY(value: number) {
    let nextValue = value
    if (Math.abs(value) < this.initialTranslateY) {
      nextValue = -1 * this.initialTranslateY
    }

    this.element.style.transform = `translateY(${nextValue}px)`;
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
    this.element.style.transition = 'transform ease 0.5s';
    this.element.classList.remove("qf-select-none")

    // Define snap points (0 = fully open, 1 = fully closed)
    const snapPoints = [0.2, 0.5, 1];

    // Current drag ratio
    const ratio = this.currentTranslateY / this.panelHeight;

    // Find closest snap point
    let closest = snapPoints[0];
    let minDiff = Math.abs(ratio - closest);
    for (const point of snapPoints) {
      const diff = Math.abs(ratio - point);
      if (diff < minDiff) {
        minDiff = diff;
        closest = point;
      }
    }

    // Snap to the closest point
    const snapY = -1 * closest * this.panelHeight;
    this.#setTranslateY(snapY);
  }
}

export default ActeurController
