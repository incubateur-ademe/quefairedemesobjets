import { Controller } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

export default class extends Controller<HTMLElement> {
  static values = {
    fieldsValues: String,
    fieldsGroups: String,
  }

  declare readonly fieldsValuesValue: string
  declare readonly fieldsGroupsValue: string

  replaceWithFieldValue(event: FocusEvent) {
    const target = event.target as HTMLElement
    const field = target.dataset.field
    const suggestionModele = target.dataset.suggestionModele
    if (!suggestionModele || !field) {
      console.error("suggestionModele ou field manquant")
      return
    }
    const value = this.#getFieldsValues()

    if (suggestionModele == "Acteur") {
      target.textContent = value[field]["acteur_target_value"] || ""
    }
    if (suggestionModele == "RevisionActeur") {
      target.textContent =
        value[field]["revision_acteur_target_value"] ||
        value[field]["acteur_target_value"]
    }
    if (suggestionModele == "ParentRevisionActeur") {
      target.textContent =
        value[field]["parent_revision_acteur_target_value"] ||
        value[field]["acteur_target_value"]
    }
  }

  saveFieldValue(event: Event) {
    const target = event.target as HTMLElement

    const suggestionModele = target.dataset.suggestionModele
    if (!suggestionModele) {
      console.error("suggestionModele manquant")
      return
    }

    const field = target.dataset.field
    if (!field) {
      console.error("field manquant")
      return
    }

    const value = target.textContent

    this.#postFieldsValues(suggestionModele, { [field]: value })
    return
  }

  updateFieldsDisplayed(event: Event) {
    const target = event.target as HTMLElement

    const suggestionModele = target.dataset.suggestionModele
    if (!suggestionModele) {
      console.error("suggestionModele manquant")
      return
    }

    const fieldsValues = this.#getFieldsValues()

    const fields = this.#getFields(event, fieldsValues)

    const newFieldsValues = {}

    for (let key of fields) {
      if (fieldsValues[key]["acteur_target_value"] !== undefined) {
        newFieldsValues[key] = fieldsValues[key]["acteur_target_value"]
      }
    }

    this.#postFieldsValues(suggestionModele, newFieldsValues)
  }

  reportUpdate(event: CustomEvent) {
    const { fields: fieldsStr, suggestionModele } = event.detail
    if (!suggestionModele || !fieldsStr) {
      console.error("suggestionModele ou fields manquant")
      return
    }

    const fieldsValues = this.#getFieldsValues()
    const fields = fieldsStr.split("|")
    const newFieldsValues = {}

    for (let key of fields) {
      if (fieldsValues[key] && fieldsValues[key]["acteur_target_value"] !== undefined) {
        newFieldsValues[key] = fieldsValues[key]["acteur_target_value"]
      }
    }

    this.#postFieldsValues(suggestionModele, newFieldsValues)
  }

  cellEditSave(event: CustomEvent) {
    const { field, suggestionModele, value } = event.detail
    if (!suggestionModele || !field) {
      console.error("suggestionModele ou field manquant")
      return
    }
    this.#postFieldsValues(suggestionModele, { [field]: value })
  }

  cellEditReplace(event: CustomEvent) {
    const { field, suggestionModele } = event.detail
    if (!suggestionModele || !field) {
      console.error("suggestionModele ou field manquant")
      return
    }
    const element = event.target as HTMLElement
    const fieldsValues = this.#getFieldsValues()

    if (suggestionModele == "Acteur") {
      element.textContent = fieldsValues[field]["acteur_target_value"] || ""
    }
    if (suggestionModele == "RevisionActeur") {
      element.textContent =
        fieldsValues[field]["revision_acteur_target_value"] ||
        fieldsValues[field]["acteur_target_value"]
    }
    if (suggestionModele == "ParentRevisionActeur") {
      element.textContent =
        fieldsValues[field]["parent_revision_acteur_target_value"] ||
        fieldsValues[field]["acteur_target_value"]
    }
  }

  updateAllDisplayed(event: Event) {
    const target = event.target as HTMLElement

    const suggestionModele = target.dataset.suggestionModele
    if (!suggestionModele) {
      console.error("suggestionModele manquant")
      return
    }

    const fieldsValues = this.#getFieldsValues()

    const newFieldsValues = {}
    for (let key in fieldsValues) {
      if (fieldsValues[key]["acteur_target_value"] !== undefined) {
        newFieldsValues[key] = fieldsValues[key]["acteur_target_value"]
      }
    }
    this.#postFieldsValues(suggestionModele, newFieldsValues)
  }

  updateStatus(event: Event) {
    const target = event.target as HTMLButtonElement
    const action = target.dataset.actionValue
    const statusUrl = target.dataset.statusUrl

    if (!action || !statusUrl) {
      console.error("Action ou URL manquante")
      return
    }

    const formData = new FormData()
    formData.append("action", action)

    this.#postSuggestion(statusUrl, formData)
  }

  handleMarkerDragged(event: CustomEvent) {
    const { latitude, longitude, markerElement } = event.detail
    const markerKey = markerElement.dataset.markerKey
    if (!latitude || !longitude) {
      console.error("Coordonnées manquantes dans l'événement")
      return
    }
    if (!markerKey) {
      console.error("Clé du marker manquante dans l'élément")
      return
    }

    const fieldsValues = {
      latitude: latitude,
      longitude: longitude,
    }

    this.#postFieldsValues(markerKey, fieldsValues, "localisation")
  }

  #getCsrfToken(): string | null {
    const match = document.cookie.match(/csrftoken=([^;]+)/)
    return match ? decodeURIComponent(match[1]) : null
  }

  #getFieldsValues() {
    const valueJson = this.fieldsValuesValue
    const value = JSON.parse(valueJson)
    return value
  }

  #getField(event: Event, fieldsValues: Record<string, any>) {
    const field = (event.target as HTMLElement).dataset.field
    if (!field) {
      console.error(
        "Champ manquant dans les attributs de l'élement, besoin de data-field",
      )
      return null
    }
    if (!(field in fieldsValues)) {
      console.error(`Champ ${field} manquant dans les valeurs`)
      return null
    }
    return field
  }

  #getFields(event: Event, fieldsValues: Record<string, any>) {
    const fields = (event.target as HTMLElement).dataset.fields
    if (!fields) {
      console.error(
        "Champ manquant dans les attributs de l'élement, besoin de data-fields",
      )
      return []
    }
    fields.split("|").forEach((field: string) => {
      if (!(field in fieldsValues)) {
        console.error(`Champ ${field} manquant dans les valeurs`)
        return []
      }
    })
    return fields.split("|")
  }

  #postFieldsValues(
    suggestionModele: string,
    fieldsValues: Record<string, any>,
    opened_tab: string = "",
  ) {
    const updateSuggestionUrl = this.element.dataset.updateSuggestionUrl
    if (!updateSuggestionUrl) {
      console.error("URL de mise à jour de la suggestion manquante")
      return
    }
    const formData = new FormData()
    const groupsJson = this.fieldsGroupsValue
    formData.append("fields_values", JSON.stringify(fieldsValues))
    formData.append("fields_groups", groupsJson)
    formData.append("suggestion_modele", suggestionModele)
    if (opened_tab) {
      formData.append("tab", opened_tab)
    }

    this.#postSuggestion(updateSuggestionUrl, formData)
  }

  #postSuggestion(postUrl: string, formData: FormData) {
    fetch(postUrl, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": this.#getCsrfToken() ?? "",
        Accept: "text/vnd.turbo-stream.html",
      },
      body: formData,
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Échec de l'appel à la route ${postUrl} : (${response.status})`,
          )
        }
        return response.text()
      })
      .then((html) => {
        Turbo.renderStreamMessage(html)
      })
      .catch((error) => {
        console.error(`Erreur lors de l'appel à la route ${postUrl} : ${error}`)
      })
  }
}
