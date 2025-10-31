import { Controller } from "@hotwired/stimulus"
import debounce from "lodash/debounce"

export default abstract class extends Controller<HTMLElement> {
  connect() {
    console.log("coucou")
  }

  search(event) {
    console.log(event.target.value)
  }
}
