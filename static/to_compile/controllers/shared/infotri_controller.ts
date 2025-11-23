import { Controller } from "@hotwired/stimulus"

/**
 * Configuration state for the Info-tri generator
 */
interface InfotriConfig {
  categorie: string
  consigne: string
  avec_phrase: boolean
}

/**
 * Stimulus controller for Info-tri generator
 *
 * This controller manages the interactive Info-tri configuration form, which allows
 * users to generate custom Info-tri labels for textile recycling.
 *
 * Features:
 * - Progressive form disclosure (each section reveals the next)
 * - Live preview updates via Turbo Frames
 * - Embed code generation for third-party sites
 * - Clipboard copy functionality
 *
 * @example
 * <div data-controller="infotri" data-infotri-base-url-value="https://example.com">
 *   <!-- Form elements -->
 * </div>
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
    "previewContainer",
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
  declare readonly previewContainerTarget: HTMLElement

  declare readonly hasConsigneSectionTarget: boolean
  declare readonly hasPhraseSectionTarget: boolean
  declare readonly hasGenerateButtonTarget: boolean
  declare readonly hasIframeTarget: boolean
  declare readonly hasPreviewContainerTarget: boolean

  declare baseUrlValue: string

  /** Current configuration state */
  private config: InfotriConfig = {
    categorie: "",
    consigne: "",
    avec_phrase: false,
  }

  /** Tracks whether the embed code has been copied */
  private copied: boolean = false

  /**
   * Lifecycle: Called when the controller is connected to the DOM
   * Initializes the UI state based on form values
   */
  connect() {
    this.updateUI()
  }

  /**
   * Event handler: Updates the selected category
   * Triggers UI update to show/hide subsequent sections
   *
   * @param event - Change event from category radio input
   */
  updateCategorie(event: Event) {
    const target = event.target as HTMLInputElement
    this.config.categorie = target.value
    this.updateUI()
  }

  /**
   * Event handler: Updates the selected consigne (disposal instruction)
   * Triggers UI update to show/hide phrase section
   *
   * @param event - Change event from consigne radio input
   */
  updateConsigne(event: Event) {
    const target = event.target as HTMLInputElement
    this.config.consigne = target.value
    this.updateUI()
  }

  /**
   * Event handler: Toggles the phrase visibility option
   *
   * @param event - Change event from phrase checkbox input
   */
  updateAvecPhrase(event: Event) {
    const target = event.target as HTMLInputElement
    this.config.avec_phrase = target.checked
    this.updateUI()
  }

  /**
   * Action: Generates and displays the embed code
   * Shows the code section with the configured iframe snippet
   */
  generate() {
    this.updateIframeCode()
    this.codeSectionTarget.classList.remove("qf-hidden")

    // Scroll the code section into view with smooth behavior
    this.codeSectionTarget.scrollIntoView({
      behavior: "smooth",
      block: "start",
    })
  }

  /**
   * Action: Copies the embed code to clipboard
   * Provides visual feedback by temporarily changing button text
   */
  async copyToClipboard() {
    try {
      const iframeCode = this.getIframeCode()
      await navigator.clipboard.writeText(iframeCode)
      this.copied = true
      this.copyButtonTarget.textContent = "Copié"

      // Reset button text after 2 seconds
      setTimeout(() => {
        this.copied = false
        this.copyButtonTarget.textContent = "Copier"
      }, 2000)
    } catch (err) {
      console.error("Failed to copy embed code to clipboard:", err)
      // Could display an error message to the user here
    }
  }

  /**
   * Updates UI visibility based on current configuration state
   * Implements progressive disclosure pattern:
   * - Consigne section appears when category is selected
   * - Phrase section appears when consigne is selected
   * - Generate button appears when consigne is selected
   * - Preview updates with each change
   */
  private updateUI() {
    // Show/hide consigne section based on category selection
    if (this.config.categorie && this.hasConsigneSectionTarget) {
      this.consigneSectionTarget.classList.remove("qf-hidden")
    } else if (this.hasConsigneSectionTarget) {
      this.consigneSectionTarget.classList.add("qf-hidden")
    }

    // Show/hide phrase section based on consigne selection
    if (this.config.consigne && this.hasPhraseSectionTarget) {
      this.phraseSectionTarget.classList.remove("qf-hidden")
    } else if (this.hasPhraseSectionTarget) {
      this.phraseSectionTarget.classList.add("qf-hidden")
    }

    // Show/hide generate button when configuration is complete
    if (this.config.consigne && this.hasGenerateButtonTarget) {
      this.generateButtonTarget.classList.remove("qf-hidden")
    } else if (this.hasGenerateButtonTarget) {
      this.generateButtonTarget.classList.add("qf-hidden")
    }

    // Update the live preview
    this.updatePreview()
  }

  /**
   * Updates the Turbo Frame preview with current configuration
   * Uses Turbo's built-in frame navigation to load the preview
   * Shows loading state during preview update
   */
  private updatePreview() {
    const params = this.buildQueryParams()
    const previewFrame = document.getElementById("infotri-preview") as HTMLElement & {
      src?: string
    }

    if (previewFrame) {
      // Show loading state
      this.showPreviewLoading()

      // Update preview URL
      previewFrame.src = `/infotri/preview?${params.toString()}`

      // Hide loading state after a short delay
      // Turbo Frame will handle the actual content loading
      setTimeout(() => {
        this.hidePreviewLoading()
      }, 300)
    }
  }

  /**
   * Shows loading indicator on preview container
   */
  private showPreviewLoading() {
    if (this.hasPreviewContainerTarget) {
      this.previewContainerTarget.classList.add(
        "qf-opacity-50",
        "qf-pointer-events-none",
      )
      this.previewContainerTarget.setAttribute("aria-busy", "true")
    }
  }

  /**
   * Hides loading indicator on preview container
   */
  private hidePreviewLoading() {
    if (this.hasPreviewContainerTarget) {
      this.previewContainerTarget.classList.remove(
        "qf-opacity-50",
        "qf-pointer-events-none",
      )
      this.previewContainerTarget.setAttribute("aria-busy", "false")
    }
  }

  /**
   * Builds query parameters from current configuration
   *
   */
  private buildQueryParams(): URLSearchParams {
    return new URLSearchParams({
      categorie: this.config.categorie,
      consigne: this.config.consigne,
      avec_phrase: this.config.avec_phrase.toString(),
    })
  }

  /**
   * Generates the embed code snippet for third-party sites
   *
   */
  private getIframeCode(): string {
    const params = this.buildQueryParams()
    return `<script src="${this.baseUrlValue}/infotri/static/infotri.js" data-config="${params.toString()}"></script>`
  }

  /**
   * Updates the displayed embed code in the UI
   */
  private updateIframeCode() {
    if (this.hasIframeTarget) {
      this.iframeTarget.textContent = this.getIframeCode()
    }
  }
}
