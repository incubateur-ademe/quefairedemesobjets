import { Controller } from "@hotwired/stimulus"

/**
 * Précharge la page visée dès que l'usager montre son intention.
 *
 * Les maquettes font de l'écran solutions une page à part entière, pas un
 * frame de la fiche : le préchargement du plan (`loading="lazy"` sur un frame)
 * ne s'applique donc plus. Un `<link rel="prefetch">` posé au survol ou au
 * premier contact obtient le même effet — le document est déjà en cache quand
 * le clic arrive — sans dupliquer bandeau et pied de page.
 *
 * Le survol précède le clic d'environ 200 ms sur pointeur, et le `touchstart`
 * d'environ 100 ms au doigt : autant de pris sur le temps d'attente.
 */
export default class extends Controller<HTMLAnchorElement> {
  private demande: HTMLLinkElement | null = null
  private modulesDemandes = false

  precharger() {
    if (this.demande || !this.element.href) return
    // `saveData` signale un forfait limité : ne pas consommer à sa place.
    if ((navigator as { connection?: { saveData?: boolean } }).connection?.saveData)
      return

    this.demande = document.createElement("link")
    this.demande.rel = "prefetch"
    this.demande.href = this.element.href
    document.head.append(this.demande)

    void this.#prechargerLaCarte()
  }

  /**
   * Met MapLibre en cache avant que l'écran carte ne le demande.
   *
   * Le document seul ne suffit pas : c'est le moteur de carte, près d'un
   * mégaoctet, qui coûte le plus à l'arrivée. L'importer ici le place dans le
   * cache du navigateur ; l'import de l'écran suivant le retrouve sans réseau.
   *
   * L'import est volontairement sans effet de bord : on ne construit aucune
   * carte, on ne fait que payer le téléchargement en avance.
   */
  async #prechargerLaCarte() {
    if (this.modulesDemandes) return
    this.modulesDemandes = true

    try {
      await Promise.all([import("maplibre-gl"), import("carte-facile")])
    } catch {
      // Un préchargement qui échoue ne doit rien casser : l'écran carte
      // refera l'import lui-même, et signalera l'erreur s'il y a lieu.
    }
  }

  disconnect() {
    this.demande?.remove()
    this.demande = null
  }
}
