import { Controller } from "@hotwired/stimulus"

/**
 * Prefetches the linked page, and the map engine it needs, on hover or first
 * touch: the click lands on a cached document.
 */
export default class extends Controller<HTMLAnchorElement> {
  private link: HTMLLinkElement | null = null
  private mapRequested = false

  prefetch() {
    if (this.link || !this.element.href) return
    if ((navigator as { connection?: { saveData?: boolean } }).connection?.saveData)
      return

    this.link = document.createElement("link")
    this.link.rel = "prefetch"
    this.link.href = this.element.href
    document.head.append(this.link)

    void this.#prefetchMap()
  }

  async #prefetchMap() {
    if (this.mapRequested) return
    this.mapRequested = true
    try {
      await import("maplibre-gl")
    } catch {
      // The map screen imports it again and reports the error.
    }
  }

  disconnect() {
    this.link?.remove()
    this.link = null
  }
}
