import debounce from "lodash/debounce"
import { Controller } from "@hotwired/stimulus"

// inspiration https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-both/
export default class extends Controller<HTMLElement> {
  static targets = ["input", "selected", "searched", "counter", "hiddenInput"]
  static values = {
    endpointUrl: String,
    emptyLabel: String,
    selectedItems: Array<String>,
  }
  declare selectedItemsValue: Array<string>
  declare readonly endpointUrlValue: string
  declare readonly emptyLabelValue: string
  declare readonly counterTarget: HTMLSpanElement
  declare readonly inputTarget: HTMLInputElement
  declare readonly searchedTarget: HTMLDivElement
  declare readonly selectedTarget: HTMLDivElement
  declare readonly hiddenInputTarget: HTMLInputElement

  // Stimulus core methods
  initialize() {
    this.search = debounce(this.search, 300).bind(this)
  }

  // Event handlers
  async search(event) {
    const request = await fetch(`${this.endpointUrlValue}${event.target.value}`)
    const results = await request.json()

    this.#resetAutocompleteItems()
    results.forEach((result: string) => {
      const autocompleteItem = this.#generateAutocompleteItem(result)
      this.searchedTarget.appendChild(autocompleteItem)
    })
  }

  selectItem(event) {
    const value = event.target.innerText

    if (this.selectedItemsValue.includes(value)) {
      return
    }

    this.selectedItemsValue = [...this.selectedItemsValue, value]
  }

  removeItem(event) {
    const value = event.target.innerText

    this.selectedItemsValue = this.selectedItemsValue.filter(
      (itemValue) => itemValue !== value,
    )
  }

  // Lifecycle
  selectedItemsValueChanged(currentValue) {
    this.#resetAutocompleteItems()
    this.#resetSearchInput()
    this.#resetSelectedItems()
    if (!currentValue.length) {
      this.selectedTarget.innerText = this.emptyLabelValue
    } else {
      currentValue.forEach((value) => {
        const selectedItem = this.#generateSelectedItem(value)
        this.selectedTarget.appendChild(selectedItem)
      })
    }
    this.#updateCounterValue()
    this.#updateHiddenInput(currentValue)
  }

  // Local methods to manipulate HTML

  #updateCounterValue() {
    this.counterTarget.innerHTML = this.selectedTarget.children.length.toString()
  }

  #updateHiddenInput(value: string) {
    this.hiddenInputTarget.value = value
  }

  #generateAutocompleteItem(value: string) {
    const autocompleteItem = document.createElement("div")
    autocompleteItem.textContent = value
    autocompleteItem.dataset.action = "click->autocomplete#selectItem"
    return autocompleteItem
  }

  #generateSelectedItem(value: string): HTMLButtonElement {
    const selectedItem = document.createElement("button")
    const classes = ["qfdmo-whitespace-nowrap", "fr-tag", "fr-tag--dismiss"]
    selectedItem.classList.add(...classes)
    selectedItem.textContent = value
    selectedItem.dataset.action = "autocomplete#removeItem"
    return selectedItem
  }

  #resetSearchInput() {
    this.inputTarget.value = ""
  }
  #resetSelectedItems() {
    this.selectedTarget.innerHTML = ""
  }

  #resetAutocompleteItems() {
    // Reset the autocomplete and remove its content
    this.searchedTarget.innerHTML = ""
  }
}
