import { Controller } from "@hotwired/stimulus"

/**
 * Submits the form as soon as a suggestion is chosen.
 *
 * The fiche mockup (30139:14478) has no button: the choice is the validation.
 * `requestSubmit` rather than `submit`, because only the former triggers HTML
 * validation: an empty required field does not go through.
 */
export default class extends Controller<HTMLFormElement> {
  submit() {
    if (this.element.requestSubmit) this.element.requestSubmit()
    else this.element.submit()
  }
}
