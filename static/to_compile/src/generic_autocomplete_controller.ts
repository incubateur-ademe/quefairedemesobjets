import debounce from "lodash/debounce"
import AutocompleteController from "./autocomplete_controller"

// inspiration https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-both/
export default class extends AutocompleteController {
  maxDisplayedResultsCount: number = 5
  static targets = [...AutocompleteController.targets, "listbox", "option"]
  static values = {
    ...AutocompleteController.values,
    displayedIds: Array,
    selectedId: String,
  }
  declare selectedIdValue: string
  declare displayedIdsValue: Array<string | null>
  declare readonly displayedIds: Array<string>
  declare readonly listboxTarget: HTMLDivElement
  declare readonly optionTargets: Array<HTMLDivElement>

  connect() {}

  initialize() {
    this.searchToComplete = debounce(this.searchToComplete, 300).bind(this)
    this.change = debounce(this.change, 300).bind(this)
    this.currentFocusedOptionIndexValue = -1
    this.selectedIdValue = JSON.parse(this.inputTarget.value)[0]
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
    if (currentValue === previousValue) {
      // This can happen when first loading the page
      return
    }

    const currentId = this.displayedIdsValue[currentValue]
    this.optionTargets.forEach((option) =>
      option.classList.remove("autocomplete-active"),
    )
    this.optionTargets
      .find((option) => option.getAttribute("id") === currentId)
      ?.classList.add("autocomplete-active")
  }

  selectedIdValueChanged(currentValue: string): void {
    this.hideAutocompleteList()
    if (currentValue && currentValue !== this.inputTarget.value) {
      this.inputTarget.value = currentValue
    }
  }

  async searchToComplete(events: Event): Promise<void> {
    this.#filterOptionsFromUserInput()
  }

  keydownEnter(event: KeyboardEvent): void {
    event.preventDefault()
    const selectedOptionId = this.#getOptionIdFrom(this.currentFocusedOptionIndexValue)
    this.selectedIdValue = selectedOptionId!
  }

  change(event): void {
    console.log("CHANGE")
    if (event.target.value.length === 0) {
      this.hideAutocompleteList()
    }
  }

  setActiveOptionFrom(event: MouseEvent): void {
    event.preventDefault()
    alert("CUCOUCOU")
    const id = event.target?.getAttribute("id")
    console.log("CLICK", id, this)
    this.selectedIdValue = id
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

  #validateUserInput() {
    if (this.inputTarget.value !== this.selectedIdValue) {
      this.inputTarget.value = ""
    }
  }

  hideAutocompleteList(event?: Event): void {
    this.#validateUserInput()
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
