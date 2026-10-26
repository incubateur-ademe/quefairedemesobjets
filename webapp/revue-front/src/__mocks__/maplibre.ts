/** Fake MapLibre for jsdom (no WebGL): markers are kept to be dragged in tests. */
type Handler = () => void

export class Marker {
  static instances: Marker[] = []
  private lngLat: [number, number] = [0, 0]
  private handlers: Record<string, Handler[]> = {}
  constructor(readonly options: { element: HTMLElement; draggable?: boolean }) {
    Marker.instances.push(this)
  }
  setLngLat(lngLat: [number, number]) {
    this.lngLat = lngLat
    return this
  }
  getLngLat() {
    return { lng: this.lngLat[0], lat: this.lngLat[1] }
  }
  addTo(map: Map) {
    map.container.appendChild(this.options.element)
    return this
  }
  remove() {
    this.options.element.remove()
    return this
  }
  on(event: string, handler: Handler) {
    ;(this.handlers[event] ??= []).push(handler)
    return this
  }
  /** Test helper: drags the marker to a position and releases it. */
  dragTo(lat: number, lng: number) {
    this.lngLat = [lng, lat]
    this.handlers.dragend?.forEach((handler) => handler())
  }
}

export class Map {
  container: HTMLElement
  constructor(options: { container: HTMLElement }) {
    this.container = options.container
  }
  addControl() {
    return this
  }
  fitBounds() {
    return this
  }
  jumpTo() {
    return this
  }
  remove() {
    this.container.innerHTML = ""
  }
}

export class LngLatBounds {
  extend() {
    return this
  }
}

export class NavigationControl {}

export function setWorkerUrl() {}
