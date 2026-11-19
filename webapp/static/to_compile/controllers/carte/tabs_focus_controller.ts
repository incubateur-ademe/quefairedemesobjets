import { Controller } from "@hotwired/stimulus"

const NAVIGATION_KEYS = ["ArrowLeft", "ArrowRight", "Home", "End"]

// DSFR selects the tab on arrow keys but leaves the focus on the previous one.
export default class extends Controller<HTMLElement> {
  followSelection(event: KeyboardEvent) {
    if (!NAVIGATION_KEYS.includes(event.key)) return
    requestAnimationFrame(() =>
      this.element
        .querySelector<HTMLElement>('[role="tab"][aria-selected="true"]')
        ?.focus(),
    )
  }
}
