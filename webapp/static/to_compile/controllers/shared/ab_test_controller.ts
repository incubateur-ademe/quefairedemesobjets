import { Controller } from "@hotwired/stimulus"
import posthog from "posthog-js"

const VARIANT_VALUE = "test"

/**
 * Generic A/B test controller for any element exposing a `src` attribute
 * (typically a `<turbo-frame>`).
 *
 * Resolves a PostHog feature flag and, when it returns "test", swaps the
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
 *     data-ab-test-src-variant-value="<variant-url>">
 *   </turbo-frame>
 *
 * Safety: if this controller never mounts (e.g. JS bundle fails) the original
 * `src` is never cleared and the element loads as if no experiment existed.
 */
export default class extends Controller<HTMLElement> {
  static values = {
    flagKey: String,
    srcVariant: String,
  }

  declare readonly flagKeyValue: string
  declare readonly srcVariantValue: string

  #controlSrc: string | null = null
  #alreadyRanOnce: boolean = false

  connect() {
    this.#controlSrc = this.element.getAttribute("src")
    if (!this.#controlSrc || !this.flagKeyValue || !this.srcVariantValue) {
      return
    }

    this.element.removeAttribute("src")

    try {
      posthog.onFeatureFlags(() => this.#resolveAndAssign())
    } catch (error) {
      console.error(error)
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

    try {
      posthog.register({ [`$feature/${this.flagKeyValue}`]: variant ?? "control" })
    } catch {
      // Tracking failure must not break the page.
    }
  }

  #assign(src: string) {
    if (this.#alreadyRanOnce) return
    this.element.setAttribute("src", src)
    this.#alreadyRanOnce = true
  }
}
