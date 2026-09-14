import { Controller } from "@hotwired/stimulus"

/**
 * Soumet le formulaire dès qu'une suggestion est choisie.
 *
 * La maquette de la fiche (30139:14478) n'a pas de bouton : le choix vaut
 * validation. `requestSubmit` plutôt que `submit`, parce que lui seul déclenche
 * la validation HTML — un champ obligatoire vide ne part donc pas.
 */
export default class extends Controller<HTMLFormElement> {
  soumettre() {
    if (this.element.requestSubmit) this.element.requestSubmit()
    else this.element.submit()
  }
}
