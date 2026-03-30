import { Controller } from "@hotwired/stimulus"
import { postFieldsValues } from "./suggestion_post"

export default class extends Controller<HTMLElement> {
  static values = {
    fields: String,
    suggestionModele: String,
    updateUrl: String,
    targetValues: { type: Object, default: {} },
    fieldsGroups: { type: Array, default: [] },
  }

  declare readonly fieldsValue: string
  declare readonly suggestionModeleValue: string
  declare readonly updateUrlValue: string
  declare readonly targetValuesValue: object
  declare readonly fieldsGroupsValue: Array<string[]>

  report() {
    postFieldsValues(
      this.element,
      this.updateUrlValue,
      this.suggestionModeleValue,
      this.targetValuesValue,
      this.fieldsGroupsValue,
    )
  }
}
