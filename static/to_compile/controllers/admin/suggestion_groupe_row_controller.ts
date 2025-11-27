import { Controller } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

export default class extends Controller<HTMLElement> {
  static targets = ["fieldsList"]

  declare readonly fieldsListTarget: HTMLInputElement

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

  refresh(event: Event) {
    console.log("refresh")
    event.preventDefault()
    event.stopPropagation()

    console.log("refresh 2")
    const refreshUrl = this.element.dataset.refreshUrl
    if (!refreshUrl) {
      console.error("URL de rafraîchissement manquante")
      return
    }

    console.log("refresh 3")
    const fieldsInput = this.fieldsListTarget
    if (!fieldsInput) {
      console.error("Champ fields_list introuvable")
      return
    }

    console.log("refresh 4")
    const formData = new FormData()
    formData.append("fields_list", fieldsInput.value)

    console.log("refresh 5", refreshUrl)
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
        console.log("refresh 6", response)
        if (!response.ok) {
          throw new Error(`Échec du rafraîchissement (${response.status})`)
        }
        return response.text()
      })
      .then((html) => {
        Turbo.renderStreamMessage(html)
      })
      .catch((error) => {
        console.log("refresh error", error)
        console.error("Erreur lors du rafraîchissement du groupe :", error)
      })
  }

  private getCsrfToken(): string | null {
    const match = document.cookie.match(/csrftoken=([^;]+)/)
    return match ? decodeURIComponent(match[1]) : null
  }
}
