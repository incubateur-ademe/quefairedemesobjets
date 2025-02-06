import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLFormElement> {
  declare readonly formTarget: HTMLFormElement
  static targets = ["form"]

  submitForm() {
    this.formTarget.requestSubmit()
  }

  clear() {
    for (const inputElement of this.formTarget.querySelectorAll("input")){
      inputElement.value =''
      this.submitForm()
    }
  }

  #move(direction: "up" | "down") {
    const searchResultAlreadyFocused = document.querySelector<HTMLAnchorElement>("#search-results > a:focus")
    let elementToFocus = document.querySelector<HTMLAnchorElement>("#search-results > a")

    if (searchResultAlreadyFocused) {
      searchResultAlreadyFocused.blur();

      if (direction == "up" && searchResultAlreadyFocused.previousElementSibling) {
        elementToFocus = searchResultAlreadyFocused.previousElementSibling as HTMLAnchorElement
      }
      else if (searchResultAlreadyFocused.nextElementSibling) {
        elementToFocus = searchResultAlreadyFocused.nextElementSibling as HTMLAnchorElement
      }
    }
    elementToFocus?.focus()
  }

  down() {
    this.#move("down")
  }

  up() {
    this.#move("up")
  }
}
