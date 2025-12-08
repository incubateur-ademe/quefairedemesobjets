import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
  static targets = ["toCopy", "button"]
  static values = {
    copied: String,
  }
  declare readonly toCopyTarget: HTMLElement
  declare readonly buttonTarget: HTMLElement
  declare readonly hasButtonTarget: boolean
  declare readonly successButtonText: string

  async toClipboard() {
    this.toCopyTarget.textContent
    await navigator.clipboard.writeText(this.toCopyTarget.textContent!)
    if (this.successButtonText) {
      this.buttonTarget.textContent = this.successButtonText
    }
  }
}
