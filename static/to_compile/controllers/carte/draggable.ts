import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
  isDragging = false
  panelHeight: number
  startY: number
  currentY: number
  startTranslateY = 0
  initialTranslateY: number
  initialTransition: string

  initialize() {
    this.panelHeight = this.element.offsetHeight
    this.initialTranslateY = this.#getPanelTranslateY()
    this.initialTransition = window.getComputedStyle(this.element).transition

    this.element.addEventListener("mousedown", this.#dragStart.bind(this))
    this.element.addEventListener('touchstart', this.#dragStart.bind(this));

    this.element.addEventListener('mousemove', this.#dragMove.bind(this));
    this.element.addEventListener('touchmove', this.#dragMove.bind(this));

    window.addEventListener('mouseup', this.#dragEnd.bind(this));
    window.addEventListener('touchend', this.#dragEnd.bind(this));
  }

  #getPanelTranslateY(): number {
    const matrix = window.getComputedStyle(this.element).transform;

    if (matrix !== 'none') {
      return Math.abs(parseFloat(matrix.split(',')[5]));
    }

    return 0
  }

  #dragStart(event: TouchEvent) {
    event.preventDefault()

    this.isDragging = true;
    const eventY = event?.y || event?.touches[0].clientY
    this.startY = Math.abs(eventY)
    this.startTranslateY = this.#getPanelTranslateY()
    this.element.style.transition = 'none';
  }

  #setTranslateY(value: number) {
    this.element.style.transform = `translateY(${value}px)`;
  }

  #dragMove(event: MouseEvent | TouchEvent) {
    event.preventDefault()

    if (!this.isDragging) return;

    // Prevent text selection the element being moved
    event.preventDefault()
    this.element.classList.add("qf-select-none")

    const eventY = event?.y || event?.touches[0].clientY
    const pixelsDragged = this.startY - eventY
    const pixelsDraggedOffsetted = pixelsDragged + this.startTranslateY
    this.currentY = Math.min(pixelsDraggedOffsetted, this.panelHeight)
    this.#setTranslateY(-1 * this.currentY);
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
    const ratio = this.currentY / this.panelHeight;

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
