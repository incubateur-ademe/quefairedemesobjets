import { Controller } from "@hotwired/stimulus"
import { getSharedData, postFieldsValues } from "./suggestion_post"

export default class extends Controller<HTMLElement> {
  static values = {
    field: String,
    suggestionModele: String,
  }

  declare readonly fieldValue: string
  declare readonly suggestionModeleValue: string

  save() {
    const value = this.element.textContent
    postFieldsValues(this.element, this.suggestionModeleValue, {
      [this.fieldValue]: value,
    })
  }

  replace() {
    const { fieldsValues } = getSharedData(this.element)
    const fieldData = fieldsValues[this.fieldValue]
    if (!fieldData) return

    if (this.suggestionModeleValue === "Acteur") {
      this.element.textContent = fieldData["acteur_target_value"] || ""
    }
    if (this.suggestionModeleValue === "RevisionActeur") {
      this.element.textContent =
        fieldData["revision_acteur_target_value"] || fieldData["acteur_target_value"]
    }
    if (this.suggestionModeleValue === "ParentRevisionActeur") {
      this.element.textContent =
        fieldData["parent_revision_acteur_target_value"] ||
        fieldData["acteur_target_value"]
    }
  }
}
