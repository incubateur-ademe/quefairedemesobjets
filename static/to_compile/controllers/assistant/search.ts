import { ClickOutsideController } from "stimulus-use"

export default class extends ClickOutsideController {
  declare readonly formTarget: HTMLFormElement
  declare readonly resultsTarget: HTMLElement
  static targets = ["form", "results"]

  submitForm() {
    this.formTarget.requestSubmit()
  }

  submitFirstItem() {
    const firstResult = this.resultsTarget.querySelector<HTMLAnchorElement>("a")
    if (firstResult) {
      firstResult.click()
    }
  }

  clear() {
    for (const inputElement of this.formTarget.querySelectorAll("input[type=text]")) {
      inputElement.value = ""
      this.submitForm()
    }
  }

  #move(direction: "up" | "down") {
    const searchResultAlreadyFocused =
      this.resultsTarget.querySelector<HTMLAnchorElement>("a:focus")
    let elementToFocus = this.resultsTarget.querySelector<HTMLAnchorElement>("a")

    if (searchResultAlreadyFocused) {
      searchResultAlreadyFocused.blur()

      if (direction == "up" && searchResultAlreadyFocused.previousElementSibling) {
        elementToFocus =
          searchResultAlreadyFocused.previousElementSibling as HTMLAnchorElement
      } else if (searchResultAlreadyFocused.nextElementSibling) {
        elementToFocus =
          searchResultAlreadyFocused.nextElementSibling as HTMLAnchorElement
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
