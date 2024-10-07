import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
  connect() {
    // TODO: pour le moment pas fonctionnel
    this.element.scrollIntoView()
  }
}
