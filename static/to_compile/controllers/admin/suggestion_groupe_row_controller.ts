import { Controller } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

export default class extends Controller<HTMLElement> {
  static values = {
    fieldsValues: String,
    fieldsGroups: String,
  }

  declare readonly fieldsValuesValue: string
  declare readonly fieldsGroupsValue: string

  fieldDisplayedFocus(event: Event) {
    const value = this.#getFieldsValues()
    const field = (event.target as HTMLElement).dataset.field
    if (!field || !(field in value)) {
      console.error("Champs manquants")
      return
    }
    const target = event.target as HTMLElement
    target.textContent =
      value[field]["updated_displayed_value"] || value[field]["displayed_value"]
  }

  fieldDisplayedBlur(event: Event) {
    const fieldsValues = this.#getFieldsValues()
    const field = this.#getField(event, fieldsValues)
    if (field != null) {
      fieldsValues[field]["updated_displayed_value"] = (
        event.target as HTMLElement
      ).textContent
      this.#postFieldsValues(fieldsValues)
    }
  }

  updateFieldsDisplayed(event: Event) {
    const fieldsValues = this.#getFieldsValues()
    const fields = this.#getFields(event, fieldsValues)
    fields.forEach((field: string) => {
      fieldsValues[field]["updated_displayed_value"] = fieldsValues[field]["new_value"]
    })
    this.#postFieldsValues(fieldsValues)
  }

  updateAllDisplayed(event: Event) {
    const fieldsValues = this.#getFieldsValues()
    for (let key in fieldsValues) {
      if (
        (fieldsValues[key]["updated_displayed_value"] === undefined &&
          fieldsValues[key]["new_value"] !== undefined) ||
        fieldsValues[key]["updated_displayed_value"] !== fieldsValues[key]["new_value"]
      ) {
        fieldsValues[key]["updated_displayed_value"] = fieldsValues[key]["new_value"]
      }
    }
    this.#postFieldsValues(fieldsValues)
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
    const { latitude, longitude } = event.detail
    if (!latitude || !longitude) {
      console.error("Coordonnées manquantes dans l'événement")
      return
    }

    const fieldsValues = this.#getFieldsValues()

    // Create the structure if it doesn't exist for latitude
    if (!("latitude" in fieldsValues)) {
      fieldsValues["latitude"] = { updated_displayed_value: "" }
    }
    fieldsValues["latitude"]["updated_displayed_value"] = latitude

    // Create the structure if it doesn't exist for longitude
    if (!("longitude" in fieldsValues)) {
      fieldsValues["longitude"] = { updated_displayed_value: "" }
    }
    fieldsValues["longitude"]["updated_displayed_value"] = longitude

    // Update the controller value to synchronize DOM
    this.fieldsValuesValue = JSON.stringify(fieldsValues)

    this.#postFieldsValues(fieldsValues, "localisation")
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

  #postFieldsValues(valuesJson: Record<string, any>, opened_tab: string = "") {
    const updateSuggestionUrl = this.element.dataset.updateSuggestionUrl
    if (!updateSuggestionUrl) {
      console.error("URL de mise à jour de la suggestion manquante")
      return
    }
    const formData = new FormData()
    const groupsJson = this.fieldsGroupsValue
    formData.append("fields_values", JSON.stringify(valuesJson))
    formData.append("fields_groups", groupsJson)
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
