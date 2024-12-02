import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLFormElement> {
  static targets = ["option"]
  declare readonly optionTargets: Array<HTMLOptionElement>

  syncSousCategorie(event) {
    const sousCategories: HTMLSelectElement = document.querySelector(
      // TODO : un peu fragile....
      "#id_proposition_services-0-sous_categories",
    )!
    const categoriesSelected = [...event.target.options]
      .filter((option) => option.selected)
      .map((option) => option.value)
    for (const sousCategorieOption of sousCategories.options) {
      if (categoriesSelected.includes(sousCategorieOption.dataset.categorie)) {
        sousCategorieOption.selected = true
      } else {
        sousCategorieOption.selected = false
      }
    }
  }
}
