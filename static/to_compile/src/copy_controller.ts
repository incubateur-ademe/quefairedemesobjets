import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
  static targets = ["toCopy", "button"]
  declare readonly toCopyTarget: HTMLElement
  declare readonly buttonTarget: HTMLElement

  async toClipboard() {
    this.toCopyTarget.textContent
    await navigator.clipboard.writeText(this.toCopyTarget.textContent!)
    this.buttonTarget.textContent = "Copié"
  }
}
