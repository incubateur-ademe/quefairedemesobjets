import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
  initialize() {
    this.element.scrollIntoView()
  }
}
