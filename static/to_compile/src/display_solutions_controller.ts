import { Controller } from "@hotwired/stimulus"

// FIXME : To be removed and set on search-solution-form controller
export default class extends Controller<HTMLElement> {
    static targets = ["loadingSolutions", "addressMissing", "NoLocalSolution"]
    declare readonly loadingSolutionsTarget: HTMLElement
    declare readonly addressMissingTarget: HTMLElement
    declare readonly NoLocalSolutionTarget: HTMLElement

    loadingSolutions() {
        this.loadingSolutionsTarget.classList.remove("qfdmo-hidden")
        this.addressMissingTarget.classList.add("qfdmo-hidden")
        this.NoLocalSolutionTarget.classList.add("qfdmo-hidden")
    }
}
