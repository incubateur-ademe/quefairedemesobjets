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
    try {
      const request = await fetch(`${this.endpointUrlValue}${event.target.value}`)
      const results = await request.json()

      this.#resetAutocompleteItems()
      results.forEach((result: string) => {
        const autocompleteItem = this.#generateAutocompleteItem(result)
        this.searchedTarget.appendChild(autocompleteItem)
      })
    } catch (error) {
      console.error("Failed to fetch autocomplete results", error)
    }
  }

  selectItem(event) {
    const value = event.target.innerText
    if (this.selectedItemsValue.includes(value)) {
      return
    }

    this.selectedItemsValue = [...this.selectedItemsValue, value]
  }

  removeItem(event) {
    const itemElement = event.currentTarget as HTMLElement
    const value = itemElement.innerText

    this.selectedItemsValue = this.selectedItemsValue.filter(
      (itemValue) => itemValue !== value,
    )
  }

  // Lifecycle methods
  selectedItemsValueChanged(currentValue) {
    this.#resetAutocompleteItems()
    this.#renderSelectedItems()
    this.#updateCounterValue()
    this.#updateHiddenInput(currentValue)
  }

  // Local methods to manipulate HTML
  #updateCounterValue() {
    this.counterTarget.innerHTML = this.selectedTarget.children.length.toString()
  }

  #updateHiddenInput(values: Array<string>) {
    this.hiddenInputTarget.innerHTML = ""
    for (const value of values) {
      const option = document.createElement("option")
      option.value = value
      option.selected = true
      this.hiddenInputTarget.appendChild(option)
    }
  }

  #generateAutocompleteItem(value: string) {
    const autocompleteItem = document.createElement("div")
    autocompleteItem.textContent = value
    autocompleteItem.dataset.action = "click->autocomplete#selectItem"
    return autocompleteItem
  }

  #generateSelectedItem(value: string): HTMLButtonElement {
    const selectedItem = document.createElement("button")
    const classes = ["qf-whitespace-nowrap", "fr-tag", "fr-tag--icon-left", "fr-icon-close-line"]
    selectedItem.classList.add(...classes)
    selectedItem.textContent = value
    selectedItem.dataset.action = "autocomplete#removeItem"
    return selectedItem
  }

  #resetAutocompleteItems() {
    this.searchedTarget.innerHTML = ""
  }

  #renderSelectedItems() {
    this.selectedTarget.innerHTML = ""
    if (this.selectedItemsValue.length === 0) {
      this.selectedTarget.textContent = this.emptyLabelValue
      return
    }

    this.selectedItemsValue.forEach((value) => {
      const item = this.#generateSelectedItem(value)
      this.selectedTarget.appendChild(item)
    })
  }
}
