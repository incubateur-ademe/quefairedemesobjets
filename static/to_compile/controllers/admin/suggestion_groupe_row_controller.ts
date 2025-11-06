import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
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
      champs.forEach((champ: HTMLInputElement) => {
        champ.value = target.dataset.champs
      })
      modelName.forEach((modelName: HTMLInputElement) => {
        modelName.value = target.dataset.modelName
      })
      form.requestSubmit()
    } else {
      console.error(`Formulaire ${formID} introuvable`)
    }
  }
}
