import { Controller } from "@hotwired/stimulus"
import { injectLocationIntoSrc, readStoredLocation } from "../../js/location_store"

/**
 * Hydrates a lazy `<turbo-frame>` with the stored location BEFORE its first
 * fetch, so the server renders results on the first (and only) request.
 *
 * A lazy frame's only pre-fetch surface is its `src` (its inner form/controllers
 * don't exist until after the fetch). This controller provides the pause-point:
 * on connect it removes `src` to pause Turbo, folds the stored location into the
 * URL, then restores `src` so the frame fetches once, located.
 *
 * IMPORTANT: the frame MUST be `loading="lazy"`. An eager frame fires its fetch
 * in `connectedCallback` during HTML parse — before Stimulus connects — so the
 * pause would come too late. `lazy` defers the fetch to viewport intersection,
 * which happens after this controller has connected.
 *
 * The AB-test frame achieves the same result by composing `injectLocationIntoSrc`
 * into its own `#assign`; this controller is for the non-AB frame, which has no
 * other controller.
 */
export default class FrameLocationController extends Controller<HTMLElement> {
  static values = { prefix: String }
  declare readonly prefixValue: string

  connect() {
    const src = this.element.getAttribute("src")
    if (!src) return // Misconfigured — leave the frame as-is.

    // Pause the frame, inject location, then let it fetch once.
    this.element.removeAttribute("src")
    this.element.setAttribute(
      "src",
      injectLocationIntoSrc(src, this.prefixValue, readStoredLocation()),
    )
  }
}
