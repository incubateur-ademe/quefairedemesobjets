import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLFormElement> {
  submitForm(event) {
    this.element.requestSubmit()
  }
}
