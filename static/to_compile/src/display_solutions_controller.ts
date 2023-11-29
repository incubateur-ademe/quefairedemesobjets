import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
    static targets = ["loadingSolutions"]
    declare readonly loadingSolutionsTarget: HTMLElement

    loadingSolutions() {
        this.loadingSolutionsTarget.classList.remove("qfdmo-hidden")
    }
}
