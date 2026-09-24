import { Controller } from "@hotwired/stimulus"

/**
 * Number of solutions behind a "Je découvre les solutions" button.
 *
 * Counting costs up to half a second on a large objet (ADR 0010): the fiche
 * renders without it, and the figure arrives afterwards. The button keeps its
 * generic label until then, so nothing depends on the request succeeding.
 *
 * With no solution nearby, the button changes style and wording but stays a
 * link: the map is still the place to look elsewhere.
 */
export default class extends Controller<HTMLAnchorElement> {
  static targets = ["libelle"]
  static values = { url: String }

  declare readonly libelleTarget: HTMLElement
  declare readonly hasLibelleTarget: boolean
  declare urlValue: string

  private pendingRequest: AbortController | null = null

  connect() {
    if (!this.urlValue || !this.hasLibelleTarget) return
    this.pendingRequest = new AbortController()
    void this.#load(this.pendingRequest.signal)
  }

  disconnect() {
    this.pendingRequest?.abort()
  }

  async #load(signal: AbortSignal) {
    try {
      const response = await fetch(this.urlValue, { signal })
      if (!response.ok) return
      const { count } = (await response.json()) as { count: number }
      this.#show(count)
    } catch {
      // A missing counter is the state the page started in: nothing to undo.
    }
  }

  #show(count: number) {
    this.element.dataset.compte = String(count)
    if (count === 0) {
      this.element.classList.replace("qfa-bouton--primaire", "qfa-bouton--secondaire")
      this.libelleTarget.textContent = "Aucune solution à proximité"
      return
    }
    this.libelleTarget.textContent =
      count === 1 ? "Je découvre la solution" : `Je découvre les ${count} solutions`
  }
}
