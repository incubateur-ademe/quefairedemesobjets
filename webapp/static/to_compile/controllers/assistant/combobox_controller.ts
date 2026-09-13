import { Controller } from "@hotwired/stimulus"
import { useClickOutside, useDebounce } from "stimulus-use"

const DELAI_FRAPPE_MS = 150

/**
 * Une suggestion. `libelle` est seul obligatoire : les champs restants
 * dépendent de l'endpoint (un slug pour un objet, des coordonnées pour une
 * adresse) et voyagent tels quels dans l'événement `choisi`.
 */
type Suggestion = {
  libelle: string
  detail?: string
  [cle: string]: unknown
}

/**
 * Combobox de saisie assistée (W3C APG combobox-autocomplete-list).
 *
 * Sert les deux champs de l'en-tête, objet et adresse : seuls l'URL interrogée
 * et la forme des suggestions changent, pas le comportement clavier ni l'ARIA.
 *
 * La liste ne s'ouvre qu'à partir de la saisie, jamais au focus : le MVP
 * (#3295) écarte explicitement la liste ouverte d'emblée.
 */
export default class extends Controller<HTMLElement> {
  static targets = ["champ", "liste", "statut", "valeur"]
  static values = {
    url: String,
    longueurMinimale: { type: Number, default: 2 },
  }

  declare readonly champTarget: HTMLInputElement
  declare readonly listeTarget: HTMLElement
  declare readonly statutTarget: HTMLElement
  declare readonly hasStatutTarget: boolean
  /** Champs cachés renseignés au choix, pour que le formulaire les soumette. */
  declare readonly valeurTargets: HTMLInputElement[]
  declare urlValue: string
  declare longueurMinimaleValue: number

  static debounces = [{ name: "chercher", wait: DELAI_FRAPPE_MS }]

  private requeteEnCours: AbortController | null = null
  private suggestions: Suggestion[] = []
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
    // Toute frappe invalide le choix précédent : sans cela, corriger le texte
    // sans re-choisir soumettrait les coordonnées de l'adresse d'avant.
    this.#oublierValeurs()

    if (saisie.length < this.longueurMinimaleValue) return this.#fermer()

    this.requeteEnCours?.abort()
    this.requeteEnCours = new AbortController()

    try {
      const reponse = await fetch(`${this.urlValue}?q=${encodeURIComponent(saisie)}`, {
        signal: this.requeteEnCours.signal,
      })
      if (!reponse.ok) throw new Error(`réponse ${reponse.status}`)
      const { resultats } = await reponse.json()
      this.suggestions = resultats
      this.#afficher()
    } catch (erreur) {
      if ((erreur as Error).name === "AbortError") return
      this.#fermer()
    }
  }

  naviguer(event: KeyboardEvent) {
    if (!this.suggestions.length) return

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
    const total = this.suggestions.length
    this.actif = ((index % total) + total) % total
    this.#afficher()
  }

  #choisir(index: number) {
    const suggestion = this.suggestions[index]
    if (!suggestion) return

    this.champTarget.value = suggestion.libelle
    this.#renseignerValeurs(suggestion)
    this.dispatch("choisi", { detail: suggestion })
    this.#fermer()
  }

  /**
   * Recopie la suggestion dans les champs cachés, par `data-cle`.
   *
   * C'est ainsi que la longitude, la latitude et le caractère précis d'une
   * adresse arrivent au serveur : l'usager ne les saisit pas, mais la carte en
   * a besoin.
   */
  #renseignerValeurs(suggestion: Suggestion) {
    for (const champ of this.valeurTargets) {
      const valeur = suggestion[champ.dataset.cle ?? ""]
      champ.value = valeur === undefined || valeur === null ? "" : String(valeur)
    }
  }

  #oublierValeurs() {
    for (const champ of this.valeurTargets) champ.value = ""
  }

  #afficher() {
    this.listeTarget.innerHTML = this.suggestions
      .map((suggestion, index) => {
        const detail = suggestion.detail
          ? ` <span class="qfa-combobox__detail">${echapper(suggestion.detail)}</span>`
          : ""
        return (
          `<li role="option" data-index="${index}" id="${this.#idOption(index)}"` +
          ` aria-selected="${index === this.actif}"` +
          ` class="qfa-combobox__option">${echapper(suggestion.libelle)}${detail}</li>`
        )
      })
      .join("")

    this.listeTarget.hidden = false
    this.champTarget.setAttribute("aria-expanded", "true")
    this.champTarget.setAttribute(
      "aria-activedescendant",
      this.actif >= 0 ? this.#idOption(this.actif) : "",
    )
    this.#annoncer(
      this.suggestions.length
        ? `${this.suggestions.length} suggestion${this.suggestions.length > 1 ? "s" : ""}`
        : "Aucune suggestion",
    )
  }

  #fermer() {
    this.listeTarget.hidden = true
    this.listeTarget.innerHTML = ""
    this.suggestions = []
    this.actif = -1
    this.champTarget.setAttribute("aria-expanded", "false")
    this.champTarget.removeAttribute("aria-activedescendant")
  }

  #idOption(index: number): string {
    return `${this.element.id || "combobox"}-option-${index}`
  }

  #annoncer(message: string) {
    if (this.hasStatutTarget) this.statutTarget.textContent = message
  }
}

/** Les libellés viennent d'une API tierce : ils ne sont pas du HTML de confiance. */
function echapper(texte: string): string {
  const noeud = document.createElement("span")
  noeud.textContent = texte
  return noeud.innerHTML
}
