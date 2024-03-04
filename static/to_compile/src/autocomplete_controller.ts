import { Controller } from "@hotwired/stimulus"
import debounce from "lodash/debounce"

export default abstract class extends Controller<HTMLElement> {
    controllerName: string = "autocomplete"
    allAvailableOptions = []
    currentFocus: number = 0
    autocompleteList: HTMLElement
    nbCharToSearchDefault: number = 3

    static targets = ["allAvailableOptions", "input", "option", "spinner"]
    declare readonly allAvailableOptionsTarget: HTMLScriptElement
    declare readonly inputTarget: HTMLInputElement
    declare readonly optionTargets: Array<HTMLElement>
    declare readonly spinnerTarget: HTMLElement

    static values = { maxOptionDisplayed: Number, nbCharToSearch: Number }
    declare readonly maxOptionDisplayedValue: number
    declare nbCharToSearchValue: number

    connect() {
        if (this.allAvailableOptionsTarget.textContent != null) {
            this.allAvailableOptions = JSON.parse(
                this.allAvailableOptionsTarget.textContent,
            )
        }
        if (!this.nbCharToSearchValue)
            this.nbCharToSearchValue = this.nbCharToSearchDefault
    }

    initialize() {
        this.search_to_complete = debounce(this.search_to_complete, 300).bind(this)
        // Delay blur event to allow click an option
        this.blurInput = debounce(this.blurInput, 300).bind(this)
    }

    async complete(events: Event): Promise<void> {
        if (this.inputTarget.value) this.displaySpinner()
        return this.search_to_complete(events)
    }

    async search_to_complete(events: Event): Promise<void> {
        const inputTargetValue = this.inputTarget.value
        const val = this.addAccents(inputTargetValue)
        const regexPattern = new RegExp(val, "gi")

        if (!val) this.closeAllLists()

        let countResult = 0

        return this.#getOptionCallback(inputTargetValue)
            .then((data) => {
                this.closeAllLists()
                this.allAvailableOptions = data
                if (this.allAvailableOptions.length == 0) return

                this.autocompleteList = this.createAutocompleteList()
                for (let i = 0; i < this.allAvailableOptions.length; i++) {
                    if (countResult >= this.maxOptionDisplayedValue) break
                    countResult++
                    this.addOption(regexPattern, this.allAvailableOptions[i])
                }
                if (this.autocompleteList.childElementCount > 0) {
                    this.currentFocus = 0
                    this.addActive()
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
        this.closeAllLists()
        this.hideSpinner()
    }

    keydownDown(event: KeyboardEvent) {
        this.currentFocus++
        this.addActive()
    }

    keydownUp(event: KeyboardEvent) {
        this.currentFocus--
        this.addActive()
    }

    keydownEnter(event: KeyboardEvent) {
        var x = document.getElementById(this.inputTarget.id + "autocomplete-list")
        let optionDiv: HTMLCollectionOf<HTMLElement> | undefined
        if (x) {
            optionDiv = x.getElementsByTagName("div")
        }

        /*If the ENTER key is pressed, prevent the form from being submitted when select an option */
        if (optionDiv !== undefined && optionDiv?.length > 0) {
            event.preventDefault()
        }
        if (this.currentFocus > -1) {
            /*and simulate a click on the "active" item:*/
            if (optionDiv) optionDiv[this.currentFocus].click()
        }
    }

    blurInput(event: Event) {
        this.closeAllLists()
    }

    closeAllLists(event?: Event) {
        var x = document.getElementsByClassName("autocomplete-items")
        for (var i = 0; i < x.length; i++) {
            x[i].remove()
        }
    }

    addActive() {
        var x: HTMLElement | null = document.getElementById(
            this.inputTarget.id + "autocomplete-list",
        )
        let optionDiv: HTMLCollectionOf<HTMLElement> | undefined
        if (x) {
            optionDiv = x.getElementsByTagName("div")
        }

        /*a function to classify an item as "active":*/
        if (!optionDiv) return false
        /*start by removing the "active" class on all items:*/
        this.#removeActive(optionDiv)
        if (this.currentFocus >= optionDiv.length) this.currentFocus = 0
        if (this.currentFocus < 0) this.currentFocus = optionDiv.length - 1
        /*add class "autocomplete-active":*/
        optionDiv[this.currentFocus].classList.add("autocomplete-active")
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
        let a = document.createElement("DIV")
        a.setAttribute("id", this.inputTarget.id + "autocomplete-list")
        a.classList.add("autocomplete-items")
        a.classList.add("qfdmo-w-full", "md:qfdmo-w-fit", "md:qfdmo-min-w-[600px]")
        /*append the DIV element as a child of the autocomplete container:*/
        this.inputTarget.after(a)
        return a
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
        this.spinnerTarget.classList.remove("qfdmo-hidden")
    }

    hideSpinner(): void {
        this.spinnerTarget.classList.add("qfdmo-hidden")
    }
}
