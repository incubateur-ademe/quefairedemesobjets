import { Controller } from "@hotwired/stimulus"

const SEUIL_MS = 50
const MESURES_CONSERVEES = 8

type Mesure = { serveur: number; total: number; lieux: number }

/**
 * Overlay de debug : durée des requêtes de lieux.
 *
 * `serveur` vient de l'en-tête `Server-Timing` renvoyé par l'endpoint, donc du
 * temps réellement passé en base. `total` inclut le réseau et la
 * désérialisation, c'est ce que ressent l'usager.
 */
export default class extends Controller<HTMLElement> {
  static targets = ["valeur", "detail"]
  static values = { seuil: { type: Number, default: SEUIL_MS } }

  declare readonly valeurTarget: HTMLElement
  declare readonly detailTarget: HTMLElement
  declare readonly hasDetailTarget: boolean
  declare seuilValue: number

  private mesures: Mesure[] = []

  mesurer(mesure: Mesure) {
    this.mesures = [mesure, ...this.mesures].slice(0, MESURES_CONSERVEES)
    this.#afficher()
  }

  #afficher() {
    const [derniere] = this.mesures
    const mediane = this.#mediane(this.mesures.map((m) => m.total))

    this.valeurTarget.textContent = `${derniere.total.toFixed(0)} ms`
    this.element.dataset.depasse = String(derniere.total > this.seuilValue)

    if (this.hasDetailTarget) {
      this.detailTarget.textContent = [
        `serveur ${derniere.serveur.toFixed(1)} ms`,
        `médiane ${mediane.toFixed(0)} ms`,
        `${derniere.lieux} lieux`,
        `budget ${this.seuilValue} ms`,
      ].join(" · ")
    }
  }

  #mediane(valeurs: number[]): number {
    const triees = [...valeurs].sort((a, b) => a - b)
    return triees[Math.floor(triees.length / 2)] ?? 0
  }
}
