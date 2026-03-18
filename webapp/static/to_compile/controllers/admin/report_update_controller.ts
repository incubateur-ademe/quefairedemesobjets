import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
  static values = {
    fields: String,
    suggestionModele: String,
  }

  declare readonly fieldsValue: string
  declare readonly suggestionModeleValue: string

  report() {
    this.dispatch("report", {
      detail: {
        fields: this.fieldsValue,
        suggestionModele: this.suggestionModeleValue,
      },
      bubbles: true,
    })
  }
}
