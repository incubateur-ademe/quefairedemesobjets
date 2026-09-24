import { Controller } from "@hotwired/stimulus"

/**
 * Prefetches the targeted page as soon as the user shows intent.
 *
 * The mockups make the solutions screen a page of its own, not a frame of the
 * fiche: the plan's prefetch (`loading="lazy"` on a frame) no longer applies.
 * A `<link rel="prefetch">` added on hover or first touch gets the same effect,
 * the document is already cached when the click lands, without duplicating
 * the header and the footer.
 *
 * Hover precedes the click by about 200 ms with a pointer, and `touchstart`
 * by about 100 ms with a finger: that much taken off the waiting time.
 */
export default class extends Controller<HTMLAnchorElement> {
  private link: HTMLLinkElement | null = null
  private modulesRequested = false

  prefetch() {
    if (this.link || !this.element.href) return
    // `saveData` signals a limited data plan: do not spend it on their behalf.
    if ((navigator as { connection?: { saveData?: boolean } }).connection?.saveData)
      return

    this.link = document.createElement("link")
    this.link.rel = "prefetch"
    this.link.href = this.element.href
    document.head.append(this.link)

    void this.#prefetchMap()
  }

  /**
   * Caches MapLibre before the map screen asks for it.
   *
   * The document alone is not enough: the map engine, close to a megabyte, is
   * what costs most on arrival. Importing it here puts it in the browser
   * cache; the next screen's import finds it without the network.
   *
   * The import is deliberately side-effect free: no map is built, only the
   * download is paid in advance.
   */
  async #prefetchMap() {
    if (this.modulesRequested) return
    this.modulesRequested = true

    try {
      await Promise.all([import("maplibre-gl"), import("carte-facile")])
    } catch {
      // A failed prefetch must break nothing: the map screen will redo the
      // import itself, and report the error if any.
    }
  }

  disconnect() {
    this.link?.remove()
    this.link = null
  }
}
