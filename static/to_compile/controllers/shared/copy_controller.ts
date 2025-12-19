import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
  static targets = ["toCopy", "button"]
  static values = {
    copied: String,
  }
  declare readonly toCopyTarget: HTMLElement
  declare readonly buttonTarget: HTMLElement
  declare readonly hasButtonTarget: boolean
  declare readonly copiedValue: string
  declare readonly hasCopiedValue: boolean

  async toClipboard() {
    await navigator.clipboard.writeText(this.toCopyTarget.textContent!)
    if (this.hasButtonTarget && this.hasCopiedValue) {
      this.buttonTarget.textContent = this.copiedValue
    }
  }
}
