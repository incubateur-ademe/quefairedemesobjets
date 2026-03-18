import { Controller } from "@hotwired/stimulus"
import { postFieldsValues } from "./suggestion_post"

export default class extends Controller<HTMLElement> {
  static values = {
    fields: String,
    suggestionModele: String,
    updateUrl: String,
    targetValues: String,
    fieldsGroups: String,
  }

  declare readonly fieldsValue: string
  declare readonly suggestionModeleValue: string
  declare readonly updateUrlValue: string
  declare readonly targetValuesValue: string
  declare readonly fieldsGroupsValue: string

  report() {
    const targetValues = JSON.parse(this.targetValuesValue || "{}")

    postFieldsValues(
      this.element,
      this.updateUrlValue,
      this.suggestionModeleValue,
      targetValues,
      this.fieldsGroupsValue,
    )
  }
}
