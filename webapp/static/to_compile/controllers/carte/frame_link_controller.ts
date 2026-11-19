import { Controller } from "@hotwired/stimulus"

type TurboFrame = HTMLElement & { src: string | null; reload(): Promise<void> }

// Loads `url` in a Turbo Frame from a <button>: a link would be announced as
// a navigation while the page URL does not change.
// Targets the frame given by `frame`, or the closest one when it is omitted.
// Once loaded, moves the focus to `focusSelector` (looked up in the frame),
// as the clicked button is replaced with the new content.
export default class extends Controller<HTMLElement> {
  static values = {
    url: String,
    frame: { type: String, default: "" },
    focusSelector: { type: String, default: "" },
  }

  declare readonly urlValue: string
  declare readonly frameValue: string
  declare readonly focusSelectorValue: string

  visit() {
    const frame = (
      this.frameValue
        ? document.getElementById(this.frameValue)
        : this.element.closest("turbo-frame")
    ) as TurboFrame | null
    if (!frame) return
    if (this.focusSelectorValue) {
      const selector = this.focusSelectorValue
      const focusWhenLoaded = (event: Event) => {
        if (event.target !== frame) return
        frame.removeEventListener("turbo:frame-load", focusWhenLoaded)
        frame.querySelector<HTMLElement>(selector)?.focus()
      }
      frame.addEventListener("turbo:frame-load", focusWhenLoaded)
    }
    if (frame.getAttribute("src") === this.urlValue) {
      void frame.reload()
    } else {
      frame.src = this.urlValue
    }
  }
}
