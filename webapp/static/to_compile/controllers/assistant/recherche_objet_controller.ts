import { Controller } from "@hotwired/stimulus"
import { useClickOutside, useDebounce } from "stimulus-use"

const DELAI_FRAPPE_MS = 150

type Resultat = { libelle: string; slug: string }

/**
 * Combobox de recherche d'objet (W3C APG combobox-autocomplete-list).
 *
 * La liste ne s'ouvre qu'à partir de la saisie, jamais au focus : le MVP
 * (#3295) écarte explicitement la liste ouverte d'emblée.
 */
export default class extends Controller<HTMLElement> {
  static targets = ["champ", "liste", "statut"]
  static values = { url: String }

  declare readonly champTarget: HTMLInputElement
  declare readonly listeTarget: HTMLElement
  declare readonly statutTarget: HTMLElement
  declare readonly hasStatutTarget: boolean
  declare urlValue: string

  static debounces = [{ name: "chercher", wait: DELAI_FRAPPE_MS }]

  private requeteEnCours: AbortController | null = null
  private resultats: Resultat[] = []
  private actif = -1

  connect() {
    useDebounce(this)
    useClickOutside(this)
  }

  disconnect() {
    this.requeteEnCours?.abort()
  }

  clickOutside() {
    this.#fermer()
  }

  async chercher() {
    const saisie = this.champTarget.value.trim()
    if (saisie.length < 2) return this.#fermer()

    this.requeteEnCours?.abort()
    this.requeteEnCours = new AbortController()

    try {
      const reponse = await fetch(`${this.urlValue}?q=${encodeURIComponent(saisie)}`, {
        signal: this.requeteEnCours.signal,
      })
      if (!reponse.ok) throw new Error(`réponse ${reponse.status}`)
      const { resultats } = await reponse.json()
      this.resultats = resultats
      this.#afficher()
    } catch (erreur) {
      if ((erreur as Error).name === "AbortError") return
      this.#fermer()
    }
  }

  naviguer(event: KeyboardEvent) {
    if (!this.resultats.length) return

    const touches: Record<string, () => void> = {
      ArrowDown: () => this.#activer(this.actif + 1),
      ArrowUp: () => this.#activer(this.actif - 1),
      Enter: () => this.#choisir(this.actif),
      Escape: () => this.#fermer(),
    }
    const action = touches[event.key]
    if (!action) return

    event.preventDefault()
    action()
  }

  choisirDepuisClic(event: MouseEvent) {
    const option = (event.target as HTMLElement).closest("[data-index]")
    if (option) this.#choisir(Number((option as HTMLElement).dataset.index))
  }

  #activer(index: number) {
    const total = this.resultats.length
    this.actif = ((index % total) + total) % total
    this.#afficher()
  }

  #choisir(index: number) {
    const resultat = this.resultats[index]
    if (!resultat) return
    this.champTarget.value = resultat.libelle
    this.dispatch("choisi", { detail: resultat })
    this.#fermer()
  }

  #afficher() {
    this.listeTarget.innerHTML = this.resultats
      .map(
        (resultat, index) =>
          `<li role="option" data-index="${index}" id="${this.#idOption(index)}"` +
          ` aria-selected="${index === this.actif}"` +
          ` class="qfa-recherche__option">${resultat.libelle}</li>`,
      )
      .join("")

    this.listeTarget.hidden = false
    this.champTarget.setAttribute("aria-expanded", "true")
    this.champTarget.setAttribute(
      "aria-activedescendant",
      this.actif >= 0 ? this.#idOption(this.actif) : "",
    )
    this.#annoncer(
      this.resultats.length
        ? `${this.resultats.length} suggestion${this.resultats.length > 1 ? "s" : ""}`
        : "Aucune suggestion",
    )
  }

  #fermer() {
    this.listeTarget.hidden = true
    this.listeTarget.innerHTML = ""
    this.resultats = []
    this.actif = -1
    this.champTarget.setAttribute("aria-expanded", "false")
    this.champTarget.removeAttribute("aria-activedescendant")
  }

  #idOption(index: number): string {
    return `${this.element.id || "recherche"}-option-${index}`
  }

  #annoncer(message: string) {
    if (this.hasStatutTarget) this.statutTarget.textContent = message
  }
}
