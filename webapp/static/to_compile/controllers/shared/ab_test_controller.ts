import { Controller } from "@hotwired/stimulus"
import posthog from "posthog-js"

const MOBILE_BREAKPOINT_QUERY = "(max-width: 767px)"
const VARIANT_VALUE = "variant"

/**
 * Generic A/B test controller for any element exposing a `src` attribute
 * (typically a `<turbo-frame>`).
 *
 * Resolves a PostHog feature flag and, when it returns "variant", swaps the
 * element's `src` for `data-ab-test-src-variant-value`. Otherwise the original
 * `src` is restored. If PostHog is unavailable or the flag cannot be resolved,
 * the original `src` is restored — the element stays equivalent to its
 * uncontrolled form.
 *
 * Markup contract:
 *   <turbo-frame
 *     src="<control-url>"
 *     data-controller="ab-test"
 *     data-ab-test-flag-key-value="my-flag"
 *     data-ab-test-src-variant-value="<variant-url>"
 *     data-ab-test-mobile-only-value="true">  <!-- optional -->
 *   </turbo-frame>
 *
 * Safety: if this controller never mounts (e.g. JS bundle fails) the original
 * `src` is never cleared and the element loads as if no experiment existed.
 */
export default class extends Controller<HTMLElement> {
  static values = {
    flagKey: String,
    srcVariant: String,
    mobileOnly: { type: Boolean, default: false },
  }

  declare readonly flagKeyValue: string
  declare readonly srcVariantValue: string
  declare readonly mobileOnlyValue: boolean

  #controlSrc: string | null = null

  connect() {
    this.#controlSrc = this.element.getAttribute("src")
    if (!this.#controlSrc || !this.flagKeyValue || !this.srcVariantValue) {
      // Misconfigured — leave the element alone so Turbo loads `src` as today.
      return
    }

    // Pause the frame until we've decided which URL to load.
    this.element.removeAttribute("src")

    if (this.mobileOnlyValue && !this.#isMobileViewport()) {
      this.#assign(this.#controlSrc)
      return
    }

    try {
      posthog.onFeatureFlags(() => this.#resolveAndAssign())
    } catch {
      this.#assign(this.#controlSrc)
    }
  }

  #resolveAndAssign() {
    let variant: string | boolean | undefined
    try {
      variant = posthog.getFeatureFlag(this.flagKeyValue)
    } catch {
      this.#assign(this.#controlSrc!)
      return
    }

    if (variant === VARIANT_VALUE) {
      this.#assign(this.srcVariantValue)
    } else {
      this.#assign(this.#controlSrc!)
    }

    // Belt-and-braces: ensure subsequent events on this page carry the variant
    // as a super-property, even if the iframe's posthog instance is separate.
    try {
      posthog.register({ [`$feature/${this.flagKeyValue}`]: variant ?? "control" })
    } catch {
      // Tracking failure must not break the page.
    }
  }

  #assign(src: string) {
    this.element.setAttribute("src", src)
  }

  #isMobileViewport(): boolean {
    if (typeof window.matchMedia !== "function") return false
    return window.matchMedia(MOBILE_BREAKPOINT_QUERY).matches
  }
}
