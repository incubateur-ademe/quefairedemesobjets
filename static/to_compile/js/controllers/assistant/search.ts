import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLFormElement> {
  submitForm(event) {
    this.element.requestSubmit()
  }
  click(event) {
    console.log({ event })
    event.target.click()
  }

  reset(event) {
    alert("coucou")
    console.log({ event })
  }
}
