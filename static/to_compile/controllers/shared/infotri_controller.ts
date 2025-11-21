import { Controller } from "@hotwired/stimulus"

/**
 * Stimulus controller for Info-tri generator
 * Manages the state of the Info-tri configuration form
 */
export default class extends Controller<HTMLElement> {
  static targets = [
    "categorieInput",
    "consigneInput",
    "avecPhraseInput",
    "categorieSection",
    "consigneSection",
    "phraseSection",
    "generateButton",
    "codeSection",
    "iframe",
    "copyButton",
  ]

  static values = {
    baseUrl: String,
  }

  declare readonly categorieInputTargets: HTMLInputElement[]
  declare readonly consigneInputTargets: HTMLInputElement[]
  declare readonly avecPhraseInputTarget: HTMLInputElement
  declare readonly categorieSectionTarget: HTMLElement
  declare readonly consigneSectionTarget: HTMLElement
  declare readonly phraseSectionTarget: HTMLElement
  declare readonly generateButtonTarget: HTMLButtonElement
  declare readonly codeSectionTarget: HTMLElement
  declare readonly iframeTarget: HTMLElement
  declare readonly copyButtonTarget: HTMLButtonElement

  declare baseUrlValue: string

  private categorie: string = ""
  private consigne: string = ""
  private avecPhrase: boolean = false
  private copied: boolean = false

  connect() {
    this.updateUI()
  }

  updateCategorie(event: Event) {
    const target = event.target as HTMLInputElement
    this.categorie = target.value
    this.updateUI()
  }

  updateConsigne(event: Event) {
    const target = event.target as HTMLInputElement
    this.consigne = target.value
    this.updateUI()
  }

  updateAvecPhrase(event: Event) {
    const target = event.target as HTMLInputElement
    this.avecPhrase = target.checked
    this.updateUI()
  }

  generate() {
    this.updateIframeCode()
    this.codeSectionTarget.classList.remove("qf-hidden")
  }

  async copyToClipboard() {
    try {
      const iframeCode = this.getIframeCode()
      await navigator.clipboard.writeText(iframeCode)
      this.copied = true
      this.copyButtonTarget.textContent = "Copié"

      // Reset after 2 seconds
      setTimeout(() => {
        this.copied = false
        this.copyButtonTarget.textContent = "Copier"
      }, 2000)
    } catch (err) {
      console.error("Failed to copy:", err)
    }
  }

  private updateUI() {
    // Show/hide consigne section
    if (this.categorie && this.hasConsigneSectionTarget) {
      this.consigneSectionTarget.classList.remove("qf-hidden")
    } else if (this.hasConsigneSectionTarget) {
      this.consigneSectionTarget.classList.add("qf-hidden")
    }

    // Show/hide phrase section
    if (this.consigne && this.hasPhraseSectionTarget) {
      this.phraseSectionTarget.classList.remove("qf-hidden")
    } else if (this.hasPhraseSectionTarget) {
      this.phraseSectionTarget.classList.add("qf-hidden")
    }

    // Show/hide generate button
    if (this.consigne && this.hasGenerateButtonTarget) {
      this.generateButtonTarget.classList.remove("qf-hidden")
    } else if (this.hasGenerateButtonTarget) {
      this.generateButtonTarget.classList.add("qf-hidden")
    }

    // Update preview
    this.updatePreview()
  }

  private updatePreview() {
    // Update the Turbo Frame with new preview
    const params = new URLSearchParams({
      categorie: this.categorie,
      consigne: this.consigne,
      avec_phrase: this.avecPhrase.toString(),
    })

    const previewFrame = document.getElementById("infotri-preview") as any
    if (previewFrame) {
      previewFrame.src = `/infotri/preview?${params.toString()}`
    }
  }

  private getIframeCode(): string {
    const params = new URLSearchParams({
      consigne: this.consigne,
      categorie: this.categorie,
      avec_phrase: this.avecPhrase.toString(),
    })

    return `<script src="${this.baseUrlValue}/infotri/static/infotri.js" data-config="${params.toString()}"></script>`
  }

  private updateIframeCode() {
    if (this.hasIframeTarget) {
      this.iframeTarget.textContent = this.getIframeCode()
    }
  }
}
