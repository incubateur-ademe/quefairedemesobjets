import debounce from "lodash/debounce"
import AutocompleteController from "./autocomplete_controller"

// inspiration https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-both/
export default class extends AutocompleteController {
  static targets = [...AutocompleteController.targets, "listbox", "option"]
  declare readonly listboxTarget: HTMLDivElement
  declare readonly optionTargets: Array<HTMLDivElement>

  #normalizeUserInput(userInput: string | null = "") {
    return userInput?.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase()
  }

  initialize() {
    this.inputTarget.setAttribute("autocomplete", "off")
  }

  connect() {
    if (!this.nbCharToSearchValue) this.nbCharToSearchValue = this.nbCharToSearchDefault
  }

  createAutocompleteList() {
    return this.listboxTarget
  }

  hideAutocompleteList(event?: Event): void {
    this.listboxTarget.classList.add("qfdmo-hidden")
    this.optionTargets.forEach(option => option.classList.add("qfdmo-hidden"))
  }

  showAutocompleteList() {
    this.listboxTarget.classList.remove("qfdmo-hidden")
  }

  async searchToComplete(events: Event): Promise<void> {
    this.showAutocompleteList()
    const userInput = this.inputTarget.value
    this.optionTargets.forEach(option => option.classList.remove("qfdmo-hidden"))
    const inactiveOptions = this.optionTargets.filter(option =>
      !this.#normalizeUserInput(option.textContent)?.includes(
        this.#normalizeUserInput(userInput)
      )
    )
    inactiveOptions.forEach(option => option.classList.add("qfdmo-hidden"))
  }
}
