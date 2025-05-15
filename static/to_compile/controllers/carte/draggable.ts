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

    window.addEventListener('mousemove', this.#dragMove.bind(this));
    window.addEventListener('touchmove', this.#dragMove.bind(this));

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

  #dragStart(event: MouseEvent | TouchEvent) {
    this.isDragging = true;
    const eventY = event?.y || event?.touches[0]
    this.startY = Math.abs(eventY)
    this.startTranslateY = this.#getPanelTranslateY()
  }

  #setTranslateY(value: number) {
    this.element.style.transform = `translateY(${value}px)`;
  }

  #dragMove(event: MouseEvent | TouchEvent) {
    if (!this.isDragging) return;
    this.element.style.transition = 'none';
    const eventY = event?.y || event?.touches[0]
    const pixelsDragged = this.startY - eventY
    const pixelsDraggedOffsetted = pixelsDragged + this.startTranslateY
    this.currentY = Math.min(pixelsDraggedOffsetted, this.panelHeight)
    this.#setTranslateY(-1 * this.currentY);
  }

  #dragEnd(event: MouseEvent | TouchEvent) {
    if (!this.isDragging) return;
    this.isDragging = false;
    this.element.style.transition = this.initialTransition;

    console.log(this.currentY, this.panelHeight, this.initialTranslateY)

    if (this.currentY > 0.6 * this.panelHeight) {
      this.#setTranslateY(-1 * this.panelHeight);
    }
    else {
      this.#setTranslateY(-1 * this.initialTranslateY)
    }
  }
}
