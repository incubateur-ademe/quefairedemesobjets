import { Controller } from "@hotwired/stimulus"
import debounce from "lodash/debounce"
import AutocompleteController from "./autocomplete_controller"
// inspiration https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-both/

export default class extends AutocompleteController<HTMLElement> {
}
