import { Controller } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

export default class extends Controller<HTMLElement> {
  static targets = ["fieldsValues", "fieldsGroups"]

  declare readonly fieldsValuesTarget: HTMLInputElement
  declare readonly fieldsGroupsTarget: HTMLInputElement

  editSuggestionGroupeRow(event: Event) {
    const target = event.target as HTMLElement

    const suggestionGroupeId = target.dataset.suggestionGroupeId
    if (!suggestionGroupeId) {
      console.error("Suggestion groupe ID manquant")
      return
    }

    const formID = `form-${target.dataset.suggestionGroupeId}`

    // Trouver le formulaire de rafraîchissement et le soumettre
    const form = document.getElementById(formID) as HTMLFormElement

    if (form) {
      // get input named valeurs and set valeurs with innerText
      const valeurs = form.querySelectorAll("input[name='valeurs']")
      const champs = form.querySelectorAll("input[name='champs']")
      const modelName = form.querySelectorAll("input[name='suggestion_modele']")
      valeurs.forEach((valeur: HTMLInputElement) => {
        valeur.value = target.innerText
      })
      const champsValue = target.dataset.champs ?? ""
      const modelNameValue = target.dataset.modelName ?? ""
      champs.forEach((champ: HTMLInputElement) => {
        champ.value = champsValue
      })
      modelName.forEach((modelName: HTMLInputElement) => {
        modelName.value = modelNameValue
      })
      form.requestSubmit()
    } else {
      console.error(`Formulaire ${formID} introuvable`)
    }
  }

  blur(event: Event) {
    console.log("blur")
  }

  #getFieldsValues() {
    const valueJson = this.fieldsValuesTarget.value
    const value = JSON.parse(valueJson)
    return value
  }

  fieldDisplayedFocus(event: Event) {
    const value = this.#getFieldsValues()
    const field = (event.target as HTMLElement).dataset.field
    if (!field || !(field in value)) {
      console.error("Champs manquants")
      return
    }
    console.log(value[field])
    const target = event.target as HTMLElement
    target.textContent =
      value[field]["updated_displayed_value"] || value[field]["displayed_value"]
  }

  fieldDisplayedBlur(event: Event) {
    const fieldsValues = this.#getFieldsValues()
    const field = (event.target as HTMLElement).dataset.field
    if (!field || !(field in fieldsValues)) {
      console.error("Champs manquants")
      return
    }
    fieldsValues[field]["updated_displayed_value"] = (
      event.target as HTMLElement
    ).textContent
    this.postFieldsValues(JSON.stringify(fieldsValues))
  }

  updateAllDisplayed(event: Event) {
    let valueJson = this.fieldsValuesTarget.value
    let value = JSON.parse(valueJson)
    for (let key in value) {
      if (
        (value[key]["updated_displayed_value"] === undefined &&
          value[key]["new_value"] !== undefined) ||
        value[key]["updated_displayed_value"] !== value[key]["new_value"]
      ) {
        value[key]["updated_displayed_value"] = value[key]["new_value"]
      }
    }
    this.postFieldsValues(JSON.stringify(value))
  }

  updateFieldsDisplayed(event: Event) {
    let valueJson = this.fieldsValuesTarget.value
    let value = JSON.parse(valueJson)
    const fields = (event.target as HTMLElement).dataset.fields
    if (!fields) {
      console.error("Champs manquants")
      return
    }
    fields.split("|").forEach((field: string) => {
      value[field]["updated_displayed_value"] = value[field]["new_value"]
    })
    this.postFieldsValues(JSON.stringify(value))
  }

  private postFieldsValues(valuesJson: string) {
    const refreshUrl = this.element.dataset.refreshUrl
    if (!refreshUrl) {
      console.error("URL de rafraîchissement manquante")
      return
    }
    const formData = new FormData()
    const groupsJson = this.fieldsGroupsTarget.value
    formData.append("fields_values", valuesJson)
    formData.append("fields_groups", groupsJson)

    fetch(refreshUrl, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": this.getCsrfToken() ?? "",
        Accept: "text/vnd.turbo-stream.html",
      },
      body: formData,
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Échec du rafraîchissement (${response.status})`)
        }
        return response.text()
      })
      .then((html) => {
        Turbo.renderStreamMessage(html)
      })
      .catch((error) => {
        console.error("Erreur lors du rafraîchissement du groupe :", error)
      })
  }

  refresh(event: Event) {
    event.preventDefault()
    event.stopPropagation()

    const refreshUrl = this.element.dataset.refreshUrl
    if (!refreshUrl) {
      console.error("URL de rafraîchissement manquante")
      return
    }

    const fieldsInput = this.fieldsListTarget
    if (!fieldsInput) {
      console.error("Champ fields_list introuvable")
      return
    }

    const formData = new FormData()
    formData.append("fields_list", fieldsInput.value)

    fetch(refreshUrl, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": this.getCsrfToken() ?? "",
        Accept: "text/vnd.turbo-stream.html",
      },
      body: formData,
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Échec du rafraîchissement (${response.status})`)
        }
        return response.text()
      })
      .then((html) => {
        Turbo.renderStreamMessage(html)
      })
      .catch((error) => {
        console.error("Erreur lors du rafraîchissement du groupe :", error)
      })
  }

  private getCsrfToken(): string | null {
    const match = document.cookie.match(/csrftoken=([^;]+)/)
    return match ? decodeURIComponent(match[1]) : null
  }
}
