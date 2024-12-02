import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLFormElement> {
  static targets = ["option"]
  declare readonly optionTargets: Array<HTMLOptionElement>

  syncSousCategorie(event) {
    console.log(event)
    const sousCategories: HTMLSelectElement = document.querySelector(
      // TODO : un peu fragile....
      "#id_proposition_services-0-sous_categories",
    )
    const valuesToSelect = [...event.target.options]
      .filter((option) => option.selected)
      .map((option) => option.value)
    for (const option of sousCategories.options) {
      if (valuesToSelect.includes(option.dataset.categorie)) {
        option.selected = true
      } else {
        option.selected = false
      }
    }
  }

  // (event) => {
  // console.log({ event })
  // })
}
