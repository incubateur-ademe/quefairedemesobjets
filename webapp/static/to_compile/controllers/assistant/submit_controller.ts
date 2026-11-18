import { Controller } from "@hotwired/stimulus"

/**
 * Submits the form as soon as a suggestion is chosen. `requestSubmit` runs
 * the HTML validation, `submit` would not.
 */
export default class extends Controller<HTMLFormElement> {
  submit() {
    this.element.requestSubmit()
  }
}
