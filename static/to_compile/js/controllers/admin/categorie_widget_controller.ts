import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLFormElement> {
  static targets = ["option"]
  declare readonly optionTargets: Array<HTMLOptionElement>

  syncSousCategorie(event) {
    const sousCategories: HTMLSelectElement = this.element
      .closest("fieldset")
      .querySelector(`select[multiple]:not(#${this.element.id})`)!

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
