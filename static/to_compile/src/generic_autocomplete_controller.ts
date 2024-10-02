import debounce from "lodash/debounce"
import AutocompleteController from "./autocomplete_controller"

// inspiration https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-both/
export default class extends AutocompleteController {
  maxDisplayedResultsCount: number = 5
  static targets = [...AutocompleteController.targets, "listbox", "option"]
  static values = {
    ...AutocompleteController.values,
    displayedIds: Array,
    selectedIds: Array,
  }
  declare selectedIdsValue: Array<string>
  declare displayedIdsValue: Array<string | null>
  declare readonly displayedIds: Array<string>
  declare readonly listboxTarget: HTMLDivElement
  declare readonly optionTargets: Array<HTMLDivElement>

  connect() {}

  initialize() {
    this.searchToComplete = debounce(this.searchToComplete, 300).bind(this)
    this.currentFocusedOptionIndexValue = -1
  }

  selectedIdsValueChanged(currentValue) {
    this.inputTarget.value = this.selectedIdsValue.join(",")
  }

  displayedIdsValueChanged(ids: Array<string>) {
    ids.forEach((id) => {
      this.optionTargets
        .filter((option) => option.getAttribute("id") === id)
        .filter((option, index) => index < this.maxDisplayedResultsCount)
        .forEach(this.#showOption)
    })
  }

  currentFocusedOptionIndexValueChanged(currentValue: string, previousValue: string) {
    if (currentValue !== previousValue) {
      const currentId = this.displayedIdsValue[currentValue]
      this.optionTargets.forEach((option) =>
        option.classList.remove("autocomplete-active"),
      )
      this.optionTargets
        .find((option) => option.getAttribute("id") === currentId)
        ?.classList.add("autocomplete-active")
    }
  }

  selectedOptionIdValueChanged(currentValue: string): void {
    if (currentValue !== this.inputTarget.value) {
      this.inputTarget.value = currentValue
    }
  }

  async searchToComplete(events: Event): Promise<void> {
    this.#filterOptionsFromUserInput()
  }

  keydownEnter(event: KeyboardEvent): void {
    const selectedOptionId = this.#getOptionIdFrom(this.currentFocusedOptionIndexValue)
    this.selectedIdsValue = [...this.selectedIdsValue, selectedOptionId!]
  }

  selectOption(event: Event): void {
    // do nothing
    // TODO: check if this method could be removed in parent class
  }

  addOption() {
    // Do nothing,
    // TODO: check if this can be removed in parent class
  }

  createAutocompleteList() {
    // TODO: rename this method in parent class
    return this.listboxTarget
  }

  hideAutocompleteList(event?: Event): void {
    this.listboxTarget.classList.add("qfdmo-hidden")
    this.optionTargets.forEach(this.#hideOption)
  }

  #normalizeUserInput(userInput: string | null = "") {
    if (!userInput) {
      return ""
    }
    return userInput
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "")
      .toLowerCase()
  }

  #openDropdown() {
    this.listboxTarget.classList.remove("qfdmo-hidden")
  }

  #showOption(option: HTMLDivElement) {
    option.classList.remove("qfdmo-hidden")
  }

  #hideOption(option: HTMLDivElement) {
    option.classList.add("qfdmo-hidden")
  }

  #getOptionIdFrom(index: number) {
    return this.displayedIdsValue[index]
  }

  #filterOptionsFromUserInput() {
    this.#openDropdown()
    const normalizedUserInput = this.#normalizeUserInput(this.inputTarget.value)

    if (!normalizedUserInput.length) {
      return
    }

    this.optionTargets.forEach(this.#hideOption)
    this.displayedIdsValue = this.optionTargets
      .filter((option) =>
        this.#normalizeUserInput(option.dataset.autocompleteSearchValue)?.includes(
          normalizedUserInput,
        ),
      )
      .map((option) => option.getAttribute("id"))
  }
}
