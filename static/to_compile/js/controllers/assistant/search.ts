import { Controller } from "@hotwired/stimulus"
import  * as Turbo from "@hotwired/turbo"

export default class extends Controller<HTMLFormElement> {
  submitForm(event) {
    this.element.requestSubmit()
  }
}
