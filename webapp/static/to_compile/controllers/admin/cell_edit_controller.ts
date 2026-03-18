import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
  static values = {
    field: String,
    suggestionModele: String,
  }

  declare readonly fieldValue: string
  declare readonly suggestionModeleValue: string

  save() {
    this.dispatch("save", {
      detail: {
        field: this.fieldValue,
        suggestionModele: this.suggestionModeleValue,
        value: this.element.textContent,
      },
      bubbles: true,
    })
  }

  replace() {
    this.dispatch("replace", {
      detail: {
        field: this.fieldValue,
        suggestionModele: this.suggestionModeleValue,
      },
      bubbles: true,
    })
  }
}
