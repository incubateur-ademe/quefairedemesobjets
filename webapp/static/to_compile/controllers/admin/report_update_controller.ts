import { Controller } from "@hotwired/stimulus"
import { getSharedData, postFieldsValues } from "./suggestion_post"

export default class extends Controller<HTMLElement> {
  static values = {
    fields: String,
    suggestionModele: String,
    updateUrl: String,
  }

  declare readonly fieldsValue: string
  declare readonly suggestionModeleValue: string
  declare readonly updateUrlValue: string

  report() {
    const { fieldsValues } = getSharedData(this.element)
    const fields = this.fieldsValue.split("|")
    const newFieldsValues: Record<string, any> = {}

    for (const key of fields) {
      if (fieldsValues[key] && fieldsValues[key]["acteur_target_value"] !== undefined) {
        newFieldsValues[key] = fieldsValues[key]["acteur_target_value"]
      }
    }

    postFieldsValues(
      this.element,
      this.updateUrlValue,
      this.suggestionModeleValue,
      newFieldsValues,
    )
  }
}
