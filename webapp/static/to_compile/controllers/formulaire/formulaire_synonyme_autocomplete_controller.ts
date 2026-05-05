import { Controller } from "@hotwired/stimulus"

interface CommitDetail {
  option: HTMLElement
  value: string
  selectedValue: string
}

export default class FormulaireSynonymeAutocompleteController extends Controller<HTMLElement> {
  static targets = ["input", "scId"]

  declare readonly inputTarget: HTMLInputElement
  declare readonly scIdTarget: HTMLInputElement

  commit(event: CustomEvent<CommitDetail>) {
    const option = event.detail.option
    const scId = option.dataset.scId ?? ""
    this.scIdTarget.value = scId
    this.dispatch("optionSelected")
  }
}
