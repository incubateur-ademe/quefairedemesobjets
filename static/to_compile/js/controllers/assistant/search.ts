import { Controller } from "@hotwired/stimulus"
import  * as Turbo from "@hotwired/turbo"

export default class extends Controller<HTMLFormElement> {
  static targets = ["input"]
  declare readonly inputTarget = HTMLInputElement

  submitForm(event) {
    this.element.requestSubmit()
  }
}
