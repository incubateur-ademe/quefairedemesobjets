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

  precharger() {
    if (this.demande || !this.element.href) return
    // `saveData` signale un forfait limité : ne pas consommer à sa place.
    if ((navigator as { connection?: { saveData?: boolean } }).connection?.saveData)
      return

    this.demande = document.createElement("link")
    this.demande.rel = "prefetch"
    this.demande.href = this.element.href
    document.head.append(this.demande)
  }

  disconnect() {
    this.demande?.remove()
    this.demande = null
  }
}
