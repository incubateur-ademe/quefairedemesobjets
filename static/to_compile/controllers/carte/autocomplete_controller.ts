import { Controller } from "@hotwired/stimulus"
import debounce from "lodash/debounce"

export default abstract class extends Controller<HTMLElement> {
  controllerName: string = "autocomplete"
  allAvailableOptions = []
  autocompleteList: HTMLElement
  nbCharToSearchDefault: number = 3

  static targets = ["allAvailableOptions", "input", "option", "spinner"]
  declare readonly allAvailableOptionsTarget: HTMLScriptElement
  declare readonly inputTarget: HTMLInputElement
  declare readonly optionTargets: Array<HTMLElement>
  declare readonly spinnerTarget: HTMLElement

  static values = {
    maxOptionDisplayed: Number,
    nbCharToSearch: Number,
    currentFocusedOptionIndex: Number,
  }
  declare readonly maxOptionDisplayedValue: number
  declare nbCharToSearchValue: number
  declare currentFocusedOptionIndexValue: number

  connect() {
    if (this.allAvailableOptionsTarget.textContent != null) {
      this.allAvailableOptions = JSON.parse(this.allAvailableOptionsTarget.textContent)
    }
    if (!this.nbCharToSearchValue) this.nbCharToSearchValue = this.nbCharToSearchDefault
  }

  initialize() {
    this.searchToComplete = debounce(this.searchToComplete, 300).bind(this)
    // Delay blur event to allow click an option
    this.blurInput = debounce(this.blurInput, 300).bind(this)
  }

  async complete(events: Event): Promise<void> {
    if (this.inputTarget.value) this.displaySpinner()
    await this.searchToComplete(events)
    this.hideSpinner()
  }

  async searchToComplete(events: Event): Promise<void> {
    const inputTargetValue = this.inputTarget.value
    const val = this.addAccents(inputTargetValue)
    const regexPattern = new RegExp(val, "gi")

    if (!val) this.hideAutocompleteList()

    let countResult = 0

    return this.#getOptionCallback(inputTargetValue)
      .then((data) => {
        this.hideAutocompleteList()
        this.allAvailableOptions = data
        if (this.allAvailableOptions.length == 0) return

        this.autocompleteList = this.createAutocompleteList()
        for (let i = 0; i < this.allAvailableOptions.length; i++) {
          if (countResult >= this.maxOptionDisplayedValue) break
          countResult++
          this.addOption(regexPattern, this.allAvailableOptions[i])
        }
        if (this.autocompleteList.childElementCount > 0) {
          this.currentFocusedOptionIndexValue = 0
        }
        return
      })
      .then(() => {
        this.hideSpinner()
        return
      })
  }

  selectOption(event: Event) {
    this.displaySpinner()
    let target = event.target as HTMLElement
    while (target && target.nodeName !== "DIV") {
      target = target.parentNode as HTMLElement
    }
    const label = target.getElementsByTagName("input")[0].value

    this.inputTarget.value = label
    this.hideAutocompleteList()
    this.hideSpinner()
  }

  keydownDown(event: KeyboardEvent) {
    this.currentFocusedOptionIndexValue++
  }

  keydownUp(event: KeyboardEvent) {
    this.currentFocusedOptionIndexValue--
  }
  currentFocusedOptionIndexValueChanged(
    currentValue: string | number,
    previousValue: string | number,
  ) {
    if (currentValue !== previousValue) {
      this.updateAutocompleteListFocusedItem()
    }
  }

  keydownEnter(event: KeyboardEvent): boolean {
    // TODO : revoir ce sélecteur qui n'est pas hyper robuste
    const autocompleteList = document.getElementById(
      this.inputTarget.id + "autocomplete-list",
    )
    let options: HTMLCollectionOf<HTMLElement> | undefined
    if (autocompleteList) {
      options = autocompleteList.getElementsByTagName("div")
    }

    /*If the ENTER key is pressed, prevent the form from being submitted when select an option */
    if (options !== undefined && options?.length > 0) {
      event.preventDefault()
      if (this.currentFocusedOptionIndexValue > -1 && options) {
        options[this.currentFocusedOptionIndexValue].click()
      }
    } else {
      return true
    }
    return false
  }

  blurInput(event: Event) {
    this.hideAutocompleteList()
  }

  hideAutocompleteList(event?: Event) {
    var x = document.getElementsByClassName("autocomplete-items")
    for (var i = 0; i < x.length; i++) {
      x[i].remove()
    }
  }

  updateAutocompleteListFocusedItem() {
    const autocompleteListWrapper: HTMLElement | null = document.getElementById(
      this.inputTarget.id + "autocomplete-list",
    )
    let optionDiv: HTMLCollectionOf<HTMLElement> | undefined
    if (autocompleteListWrapper) {
      optionDiv = autocompleteListWrapper.getElementsByTagName("div")
    }

    /*a function to classify an item as "active":*/
    if (!optionDiv) return false
    /*start by removing the "active" class on all items:*/
    this.#removeActive(optionDiv)
    if (this.currentFocusedOptionIndexValue >= optionDiv.length) this.currentFocusedOptionIndexValue = 0
    if (this.currentFocusedOptionIndexValue < 0) this.currentFocusedOptionIndexValue = optionDiv.length - 1
    /*add class "autocomplete-active":*/
    optionDiv[this.currentFocusedOptionIndexValue].classList.add("autocomplete-active")
  }

  addAccents(input: string) {
    let retval = input
    // Escape special characters first
    retval = retval.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    // List all accentuated characters possible
    retval = retval.replace(/([ao])e/gi, "$1")
    retval = retval.replace(/e/gi, "[eèéêë]")
    retval = retval.replace(/c/gi, "[cç]")
    retval = retval.replace(/i/gi, "[iîï]")
    retval = retval.replace(/u/gi, "[uùûü]")
    retval = retval.replace(/y/gi, "[yÿ]")
    retval = retval.replace(/s/gi, "(ss|[sß])")
    retval = retval.replace(/a/gi, "([aàâä]|ae)")
    retval = retval.replace(/o/gi, "([oôö]|oe)")
    return retval
  }

  addOption(regexPattern: RegExp, option: any) {
    // Implement this method in your controller
  }

  createAutocompleteList() {
    /*create a DIV element that will contain the items (values):*/
     const autocompleteDivWrapper = document.createElement("DIV")
     autocompleteDivWrapper.setAttribute("id", this.inputTarget.id + "autocomplete-list")
     autocompleteDivWrapper.classList.add("autocomplete-items")

     const inputTargetWidth = this.inputTarget.offsetWidth
     autocompleteDivWrapper.classList.add("qf-w-full")
     autocompleteDivWrapper.style.width = `${inputTargetWidth}px`

     /*append the DIV element as a child of the autocomplete container:*/
     this.inputTarget.after(autocompleteDivWrapper)
     return autocompleteDivWrapper
   }

  #removeActive(optionDiv: HTMLCollectionOf<HTMLElement>) {
    for (var i = 0; i < optionDiv.length; i++) {
      optionDiv[i].classList.remove("autocomplete-active")
    }
  }

  async #getOptionCallback(value: string): Promise<string[]> {
    // Implement this method in your controller
    return []

  }

  displaySpinner(): void {
    this.spinnerTarget.classList.remove("qf-hidden")
  }

  hideSpinner(): void {
    this.spinnerTarget.classList.add("qf-hidden")
  }
}
