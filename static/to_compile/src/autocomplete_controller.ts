import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    controllerName: string = "autocomplete"
    allAvailableOptions: Array<string> = []
    currentFocus: number = 0
    autocompleteList: HTMLElement
    nbCharToSearchDefault: number = 3

    static targets = ["allAvailableOptions", "input", "option"]
    declare readonly allAvailableOptionsTarget: HTMLScriptElement
    declare readonly inputTarget: HTMLInputElement
    declare readonly optionTargets: Array<HTMLElement>

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

    async complete(events: Event): Promise<boolean> {
        const inputTargetValue = this.inputTarget.value
        const val = this.addAccents(inputTargetValue)
        const regexPattern = new RegExp(val, "gi")

        if (!val) {
            this.closeAllLists()
        }

        let countResult = 0

        this.#getOptionCallback(inputTargetValue).then((data) => {
            this.closeAllLists()
            this.allAvailableOptions = data
            if (this.allAvailableOptions.length == 0) return

            this.autocompleteList = this.createAutocompleteList()
            for (let i = 0; i < this.allAvailableOptions.length; i++) {
                if (countResult >= this.maxOptionDisplayedValue) break
                countResult++
                this.addoption(regexPattern, this.allAvailableOptions[i])
            }
            if (this.autocompleteList.childElementCount > 0) {
                this.currentFocus = 0
                this.addActive()
            }
        })
        return true
    }

    selectOption(event: Event) {
        let target = event.target as HTMLElement
        const label = target.getElementsByTagName("input")[0].value

        this.inputTarget.value = label
        this.closeAllLists()
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

    closeAllLists() {
        var x = document.getElementsByClassName("autocomplete-items")
        for (var i = 0; i < x.length; i++) {
            x[i].remove()
        }
    }

    closeListsOnFocusOut(event: Event) {
        const target = event.target as Element
        if (target.getAttribute("data-on-focus")) return
        this.closeAllLists()
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

    addoption(regexPattern: RegExp, option: string) {
        //option : this.#allAvailableOptions[i]
        /*create a DIV element for each matching element:*/
        let b = document.createElement("DIV")
        /*make the matching letters bold:*/
        const [data, longitude, latitude] = option.split("||")
        const newText = data.replace(regexPattern, "<strong>$&</strong>")
        b.innerHTML = newText
        // FIXME : better way to do this
        const input = document.createElement("input")
        input.setAttribute("type", "hidden")
        input.setAttribute("value", option)
        b.appendChild(input)
        b.setAttribute("data-action", "click->" + this.controllerName + "#selectOption")
        b.setAttribute("data-on-focus", "true")
        this.autocompleteList.appendChild(b)
    }

    createAutocompleteList() {
        /*create a DIV element that will contain the items (values):*/
        let a = document.createElement("DIV")
        a.setAttribute("id", this.inputTarget.id + "autocomplete-list")
        a.setAttribute("class", "autocomplete-items")
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
        if (value.trim().length < this.nbCharToSearchValue) return []
        return await fetch(`/qfdmo/get_object_list?q=${value}`)
            .then((response) => response.json())
            .then((data) => {
                return data
            })
            .catch((error) => {
                console.error("error catched : ", error)
                return []
            })
    }
}
