import "@testing-library/jest-dom"

import { Application } from "@hotwired/stimulus"
import InfotriController from "../controllers/shared/infotri_controller"

describe("InfotriController", () => {
  let application: Application
  let container: HTMLElement

  beforeEach(() => {
    document.body.innerHTML = `
      <div data-controller="infotri" data-infotri-base-url-value="https://example.com">
        <div data-infotri-target="categorieSection">
          <input type="radio" name="categorie" value="tous" data-action="change->infotri#updateCategorie" data-infotri-target="categorieInput">
          <input type="radio" name="categorie" value="vetement" data-action="change->infotri#updateCategorie" data-infotri-target="categorieInput">
        </div>

        <div data-infotri-target="consigneSection" class="qf-hidden">
          <input type="radio" name="consigne" value="1" data-action="change->infotri#updateConsigne" data-infotri-target="consigneInput">
          <input type="radio" name="consigne" value="2" data-action="change->infotri#updateConsigne" data-infotri-target="consigneInput">
        </div>

        <div data-infotri-target="phraseSection" class="qf-hidden">
          <input type="checkbox" name="avec_phrase" data-action="change->infotri#updateAvecPhrase" data-infotri-target="avecPhraseInput">
        </div>

        <button data-infotri-target="generateButton" data-action="click->infotri#generate" class="qf-hidden">Générer</button>

        <div data-infotri-target="codeSection" class="qf-hidden">
          <pre data-infotri-target="iframe"></pre>
          <button data-infotri-target="copyButton" data-action="click->infotri#copyToClipboard">Copier</button>
        </div>

        <div data-infotri-target="previewContainer">
          <turbo-frame id="infotri-preview" src="/infotri/preview"></turbo-frame>
        </div>
      </div>
    `

    application = Application.start()
    application.register("infotri", InfotriController)
    container = document.querySelector('[data-controller="infotri"]') as HTMLElement
  })

  afterEach(() => {
    application.stop()
  })

  describe("Progressive disclosure", () => {
    it("should hide consigne and phrase sections initially", async () => {
      await new Promise((r) => setTimeout(r, 0))

      const consigneSection = container.querySelector(
        '[data-infotri-target="consigneSection"]',
      )
      const phraseSection = container.querySelector(
        '[data-infotri-target="phraseSection"]',
      )

      expect(consigneSection).toHaveClass("qf-hidden")
      expect(phraseSection).toHaveClass("qf-hidden")
    })

    it("should show consigne section when category is selected", async () => {
      const categorieInput = container.querySelector(
        'input[name="categorie"][value="tous"]',
      ) as HTMLInputElement

      categorieInput.click()
      await new Promise((r) => setTimeout(r, 0))

      const consigneSection = container.querySelector(
        '[data-infotri-target="consigneSection"]',
      )
      expect(consigneSection).not.toHaveClass("qf-hidden")
    })

    it("should show phrase section when consigne is selected", async () => {
      const categorieInput = container.querySelector(
        'input[name="categorie"][value="tous"]',
      ) as HTMLInputElement
      const consigneInput = container.querySelector(
        'input[name="consigne"][value="1"]',
      ) as HTMLInputElement

      categorieInput.click()
      await new Promise((r) => setTimeout(r, 0))

      consigneInput.click()
      await new Promise((r) => setTimeout(r, 0))

      const phraseSection = container.querySelector(
        '[data-infotri-target="phraseSection"]',
      )
      expect(phraseSection).not.toHaveClass("qf-hidden")
    })

    it("should show generate button when consigne is selected", async () => {
      const categorieInput = container.querySelector(
        'input[name="categorie"][value="tous"]',
      ) as HTMLInputElement
      const consigneInput = container.querySelector(
        'input[name="consigne"][value="1"]',
      ) as HTMLInputElement

      categorieInput.click()
      await new Promise((r) => setTimeout(r, 0))

      consigneInput.click()
      await new Promise((r) => setTimeout(r, 0))

      const generateButton = container.querySelector(
        '[data-infotri-target="generateButton"]',
      )
      expect(generateButton).not.toHaveClass("qf-hidden")
    })
  })

  describe("Configuration updates", () => {
    it("should update config when category changes", async () => {
      const categorieInput = container.querySelector(
        'input[name="categorie"][value="vetement"]',
      ) as HTMLInputElement

      categorieInput.click()
      await new Promise((r) => setTimeout(r, 0))

      expect(categorieInput.checked).toBe(true)
    })

    it("should update config when consigne changes", async () => {
      const categorieInput = container.querySelector(
        'input[name="categorie"][value="tous"]',
      ) as HTMLInputElement
      const consigneInput = container.querySelector(
        'input[name="consigne"][value="2"]',
      ) as HTMLInputElement

      categorieInput.click()
      await new Promise((r) => setTimeout(r, 0))

      consigneInput.click()
      await new Promise((r) => setTimeout(r, 0))

      expect(consigneInput.checked).toBe(true)
    })

    it("should update config when phrase checkbox changes", async () => {
      const avecPhraseInput = container.querySelector(
        'input[name="avec_phrase"]',
      ) as HTMLInputElement

      avecPhraseInput.click()
      await new Promise((r) => setTimeout(r, 0))

      expect(avecPhraseInput.checked).toBe(true)
    })
  })

  describe("Code generation", () => {
    it("should generate correct embed code with all fields filled", async () => {
      const categorieInput = container.querySelector(
        'input[name="categorie"][value="tous"]',
      ) as HTMLInputElement
      const consigneInput = container.querySelector(
        'input[name="consigne"][value="1"]',
      ) as HTMLInputElement
      const avecPhraseInput = container.querySelector(
        'input[name="avec_phrase"]',
      ) as HTMLInputElement
      const generateButton = container.querySelector(
        '[data-infotri-target="generateButton"]',
      ) as HTMLButtonElement

      categorieInput.click()
      await new Promise((r) => setTimeout(r, 0))

      consigneInput.click()
      await new Promise((r) => setTimeout(r, 0))

      avecPhraseInput.click()
      await new Promise((r) => setTimeout(r, 0))

      generateButton.click()
      await new Promise((r) => setTimeout(r, 0))

      const codeSection = container.querySelector('[data-infotri-target="codeSection"]')
      const iframeCode = container.querySelector('[data-infotri-target="iframe"]')

      expect(codeSection).not.toHaveClass("qf-hidden")
      expect(iframeCode?.textContent).toContain(
        'src="https://example.com/infotri/static/infotri.js"',
      )
      expect(iframeCode?.textContent).toContain("categorie=tous")
      expect(iframeCode?.textContent).toContain("consigne=1")
      expect(iframeCode?.textContent).toContain("avec_phrase=true")
    })

    it("should generate correct embed code with phrase disabled", async () => {
      const categorieInput = container.querySelector(
        'input[name="categorie"][value="vetement"]',
      ) as HTMLInputElement
      const consigneInput = container.querySelector(
        'input[name="consigne"][value="2"]',
      ) as HTMLInputElement
      const generateButton = container.querySelector(
        '[data-infotri-target="generateButton"]',
      ) as HTMLButtonElement

      categorieInput.click()
      await new Promise((r) => setTimeout(r, 0))

      consigneInput.click()
      await new Promise((r) => setTimeout(r, 0))

      generateButton.click()
      await new Promise((r) => setTimeout(r, 0))

      const iframeCode = container.querySelector('[data-infotri-target="iframe"]')

      expect(iframeCode?.textContent).toContain("categorie=vetement")
      expect(iframeCode?.textContent).toContain("consigne=2")
      expect(iframeCode?.textContent).toContain("avec_phrase=false")
    })
  })

  describe("Copy functionality", () => {
    it("should copy embed code to clipboard", async () => {
      Object.assign(navigator, {
        clipboard: {
          writeText: jest.fn().mockResolvedValue(undefined),
        },
      })

      const categorieInput = container.querySelector(
        'input[name="categorie"][value="tous"]',
      ) as HTMLInputElement
      const consigneInput = container.querySelector(
        'input[name="consigne"][value="1"]',
      ) as HTMLInputElement
      const generateButton = container.querySelector(
        '[data-infotri-target="generateButton"]',
      ) as HTMLButtonElement

      categorieInput.click()
      await new Promise((r) => setTimeout(r, 0))

      consigneInput.click()
      await new Promise((r) => setTimeout(r, 0))

      generateButton.click()
      await new Promise((r) => setTimeout(r, 0))

      const copyButton = container.querySelector(
        '[data-infotri-target="copyButton"]',
      ) as HTMLButtonElement

      copyButton.click()
      await new Promise((r) => setTimeout(r, 0))

      expect(navigator.clipboard.writeText).toHaveBeenCalled()
      expect(copyButton.textContent).toBe("Copié")

      // Wait for button text to reset
      await new Promise((r) => setTimeout(r, 2100))
      expect(copyButton.textContent).toBe("Copier")
    })
  })
})
