import { Controller } from "@hotwired/stimulus"
import { postFieldsValues } from "./suggestion_post"

export default class extends Controller<HTMLElement> {
  static values = {
    field: String,
    suggestionModele: String,
    updateUrl: String,
    replaceText: String,
    fieldsGroups: { type: Array, default: [] },
    identifiantUnique: String,
  }

  declare readonly fieldValue: string
  declare readonly suggestionModeleValue: string
  declare readonly updateUrlValue: string
  declare readonly replaceTextValue: string
  declare readonly fieldsGroupsValue: Array<string[]>
  declare readonly identifiantUniqueValue: string

  save() {
    const value = this.element.textContent
    postFieldsValues(
      this.element,
      this.updateUrlValue,
      this.suggestionModeleValue,
      { [this.fieldValue]: value },
      this.fieldsGroupsValue,
      "",
      this.identifiantUniqueValue,
    )
  }

  replace() {
    this.element.textContent = this.replaceTextValue
  }
}
