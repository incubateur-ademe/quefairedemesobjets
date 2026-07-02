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
 * The frame MUST start as `loading="lazy"` so Turbo doesn't fire its fetch in
 * `connectedCallback` during HTML parse (before Stimulus connects). Once this
 * controller has injected the location, it strips `loading="lazy"` so the frame
 * loads eagerly on the final `src` — the IntersectionObserver may have already
 * fired by now, and a lazy frame that re-enters the viewport after a `src`
 * change won't re-trigger loading on its own.
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

    // Pause the frame, inject location.
    this.element.removeAttribute("src")
    const finalSrc = injectLocationIntoSrc(src, this.prefixValue, readStoredLocation())
    this.element.setAttribute("src", finalSrc)

    // Strip `loading="lazy"` so Turbo loads the frame eagerly. By this
    // point the IntersectionObserver may have already fired (the element
    // was in the viewport at parse time), and a lazy frame won't reload
    // on its own when `src` changes post-intersection.
    this.element.removeAttribute("loading")
  }
}
