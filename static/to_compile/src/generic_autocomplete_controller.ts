import debounce from "lodash/debounce"
import AutocompleteController from "./autocomplete_controller"

// inspiration https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-both/
export default class extends AutocompleteController {
  maxDisplayedResultsCount: number = 5
  static targets = [...AutocompleteController.targets, "listbox", "option"]
  static values = {
    ...AutocompleteController.values,
    displayedOptionsIds: Array,
    selectedOptionsIds: Array,
    selectedOptionId: String,
  }
  declare selectedOptionIdValue: string
  declare selectedOptionsIdsValue: Array<string>
  declare displayedOptionsIdsValue: Array<string | null>
  declare readonly displayedOptionsIds: Array<string>
  declare readonly listboxTarget: HTMLDivElement
  declare readonly optionTargets: Array<HTMLDivElement>

  connect() {}

  initialize() {
    this.searchToComplete = debounce(this.searchToComplete, 300).bind(this)
    this.currentFocusedOptionIndexValue = -1
  }

  selectedOptionIdsValueChanged(currentValue) {
    console.log("selected options ids value changed")
    this.inputTarget.value = currentValue
  }

  displayedOptionsIdsValueChanged(ids: Array<string>) {
    ids.forEach((id) => {
      this.optionTargets
        .filter((option) => option.getAttribute("id") === id)
        .filter((option, index) => index < this.maxDisplayedResultsCount)
        .forEach(this.#showOption)
    })
  }

  currentFocusedOptionIndexValueChanged(currentValue: string, previousValue: string) {
    console.log("COUCOU", this.displayedOptionsIdsValue)
    if (currentValue !== previousValue) {
      const currentId = this.displayedOptionsIdsValue[currentValue]
      console.log({ currentId, currentValue }, this.displayedOptionsIdsValue)
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
    this.selectedOptionsIdsValue
      .push
      // this.#getOptionIdFrom(this.currentFocusedOptionIndexValue),
      ()
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
    console.log("SHOW OPTION", { option })
    option.classList.remove("qfdmo-hidden")
  }

  #hideOption(option: HTMLDivElement) {
    option.classList.add("qfdmo-hidden")
  }

  #getOptionIdFrom(index: number) {
    return this.displayedOptionsIds[index]
  }

  #filterOptionsFromUserInput() {
    this.#openDropdown()
    const normalizedUserInput = this.#normalizeUserInput(this.inputTarget.value)

    if (!normalizedUserInput.length) {
      return
    }

    this.optionTargets.forEach(this.#hideOption)
    this.displayedOptionsIdsValue = this.optionTargets
      .filter((option) =>
        this.#normalizeUserInput(option.dataset.autocompleteSearchValue)?.includes(
          normalizedUserInput,
        ),
      )
      .map((option) => option.getAttribute("id"))
  }
}
