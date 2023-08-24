import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    #allAvailableOptions: Array<String> = []
    #currentFocus: number = 0

    static targets = ["allAvailableOptions", "input", "option"]
    declare readonly allAvailableOptionsTarget: HTMLScriptElement
    declare readonly inputTarget: HTMLInputElement
    declare readonly optionTargets: Array<HTMLElement>

    static values = { maxOptionDisplayed: Number }
    declare readonly maxOptionDisplayedValue: number

    connect() {
        if (this.allAvailableOptionsTarget.textContent != null) {
            this.#allAvailableOptions = JSON.parse(
                this.allAvailableOptionsTarget.textContent,
            )
        }
    }

    complete(events: Event) {
        let val = this.inputTarget.value

        //clear previous option list
        var x = document.getElementsByClassName("autocomplete-items")
        for (var i = 0; i < x.length; i++) {
            x[i].remove()
        }
        if (!val) {
            return false
        }

        /*create a DIV element that will contain the items (values):*/
        let a = document.createElement("DIV")
        a.setAttribute("id", this.inputTarget.id + "autocomplete-list")
        a.setAttribute("class", "autocomplete-items")
        /*append the DIV element as a child of the autocomplete container:*/
        if (this.inputTarget.parentNode != null) {
            this.inputTarget.parentNode.appendChild(a)
        }
        /*for each item in the array...*/
        let countResult = 0
        for (let i = 0; i < this.#allAvailableOptions.length; i++) {
            if (countResult >= this.maxOptionDisplayedValue) break
            /*check if the item starts with the same letters as the text field value:*/
            if (
                this.#allAvailableOptions[i].toLowerCase().includes(val.toLowerCase())
            ) {
                countResult++
                /*create a DIV element for each matching element:*/
                let b = document.createElement("DIV")
                /*make the matching letters bold:*/
                const regexPattern = new RegExp(val, "gi")
                const newText = this.#allAvailableOptions[i].replace(
                    regexPattern,
                    "<strong>$&</strong>",
                )
                b.innerHTML = newText
                // FIXME : better way to do this
                b.innerHTML +=
                    "<input type='hidden' value='" + this.#allAvailableOptions[i] + "'>"
                b.setAttribute("data-action", "click->autocomplete#selectOption")
                a.appendChild(b)
            }
        }
        // FIXME : check if list is empty
        if (a.childElementCount > 0) {
            this.#currentFocus = 0
            this.#addActive()
        }
    }

    selectOption(event: Event) {
        let target = event.target as HTMLElement
        this.inputTarget.value = target.getElementsByTagName("input")[0].value
        this.#closeAllLists()
    }

    keydownDown(event: KeyboardEvent) {
        this.#currentFocus++
        this.#addActive()
    }

    keydownUp(event: KeyboardEvent) {
        this.#currentFocus--
        this.#addActive()
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
        if (this.#currentFocus > -1) {
            /*and simulate a click on the "active" item:*/
            if (optionDiv) optionDiv[this.#currentFocus].click()
        }
    }

    #closeAllLists() {
        var x = document.getElementsByClassName("autocomplete-items")
        for (var i = 0; i < x.length; i++) {
            x[i].remove()
        }
    }

    #addActive() {
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
        if (this.#currentFocus >= optionDiv.length) this.#currentFocus = 0
        if (this.#currentFocus < 0) this.#currentFocus = optionDiv.length - 1
        /*add class "autocomplete-active":*/
        optionDiv[this.#currentFocus].classList.add("autocomplete-active")
    }

    #removeActive(optionDiv) {
        for (var i = 0; i < optionDiv.length; i++) {
            optionDiv[i].classList.remove("autocomplete-active")
        }
    }
}
