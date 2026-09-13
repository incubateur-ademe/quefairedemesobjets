import { Controller } from "@hotwired/stimulus"
import { useDebounce, useResize } from "stimulus-use"

import {
  fusionner,
  lieuxDepuisGeoJSON,
  type Lieu,
  type Zone,
} from "../../js/assistant/lieux_visibles"
import { elementPinpoint, type CouleursPinpoint } from "../../js/assistant/pinpoint"
import type { Map as CarteMapLibre, Marker } from "maplibre-gl"

type Mesure = { serveur: number; total: number; lieux: number }

/** Lit `acteurs;dur=12.3` dans l'en-tête Server-Timing. */
function dureeServeur(entete: string | null): number {
  const correspondance = entete?.match(/acteurs;dur=([\d.]+)/)
  return correspondance ? Number(correspondance[1]) : 0
}

const DELAI_STABILISATION_MS = 1000
const ZOOM_MINIMUM = 9

export default class extends Controller<HTMLElement> {
  static targets = ["conteneur", "message"]
  static values = {
    url: String,
    geste: String,
    objet: String,
    longitude: Number,
    latitude: Number,
  }
  static outlets = ["assistant-chrono"]
  static debounces = [{ name: "rafraichir", wait: DELAI_STABILISATION_MS }]

  declare readonly assistantChronoOutlets: { mesurer(mesure: Mesure): void }[]
  declare readonly conteneurTarget: HTMLElement
  declare readonly messageTarget: HTMLElement
  declare readonly hasMessageTarget: boolean
  declare urlValue: string
  declare gesteValue: string
  declare objetValue: string
  declare longitudeValue: number
  declare latitudeValue: number

  private carte: CarteMapLibre | null = null
  private Marqueur!: typeof Marker
  private marqueurs = new Map<string, Marker>()
  private lieux: Lieu[] = []
  private requeteEnCours: AbortController | null = null

  async connect() {
    useDebounce(this)
    useResize(this)

    const { Map, Marker, NavigationControl } = await import("maplibre-gl")
    this.Marqueur = Marker
    const { mapStyles } = await import("carte-facile")

    this.carte = new Map({
      container: this.conteneurTarget,
      style: mapStyles.desaturated,
      center: [this.longitudeValue, this.latitudeValue],
      zoom: 13,
      attributionControl: { compact: true },
    })
    this.carte.addControl(new NavigationControl({ showCompass: false }), "top-left")
    await this.carte.once("load")

    // MapLibre mesure son conteneur à la construction, avant que la feuille de
    // styles ne soit forcément appliquée. Sans ce resize, la zone visible
    // calculée est celle d'un conteneur trop haut et les lieux ramenés tombent
    // hors de l'écran.
    this.carte.resize()

    // L'écoute de `moveend` n'est branchée qu'après le resize : celui-ci émet
    // un `moveend`, qui déclencherait un second chargement identique au
    // premier, une seconde plus tard.
    this.carte.on("moveend", () => this.rafraichir())
    await this.#charger()
  }

  disconnect() {
    this.requeteEnCours?.abort()
    this.marqueurs.forEach((marqueur) => marqueur.remove())
    this.marqueurs.clear()
    this.carte?.remove()
    this.carte = null
  }

  resize() {
    this.carte?.resize()
  }

  /** Débouncée : appelée à chaque `moveend`, n'agit qu'une fois la carte stable. */
  rafraichir() {
    void this.#charger()
  }

  async #charger() {
    if (!this.carte) return

    if (this.carte.getZoom() < ZOOM_MINIMUM) {
      this.#masquerMarqueurs()
      this.#annoncer(
        "Zoomez sur la carte et faites-la défiler, ou cherchez une nouvelle adresse pour voir apparaître des points.",
      )
      return
    }

    this.requeteEnCours?.abort()
    this.requeteEnCours = new AbortController()

    const debut = performance.now()
    try {
      const reponse = await fetch(this.#urlDesLieux(), {
        signal: this.requeteEnCours.signal,
      })
      if (!reponse.ok) throw new Error(`réponse ${reponse.status}`)

      const nouveaux = lieuxDepuisGeoJSON(await reponse.json())
      const mesure = {
        serveur: dureeServeur(reponse.headers.get("Server-Timing")),
        total: performance.now() - debut,
        lieux: nouveaux.length,
      }
      this.assistantChronoOutlets.forEach((chrono) => chrono.mesurer(mesure))
      this.lieux = fusionner(this.lieux, nouveaux, this.#zoneVisible())
      this.#dessiner()
      this.#annoncer(
        this.lieux.length
          ? ""
          : "Aucun lieu trouvé ici. Déplacez la carte pour explorer une autre zone.",
      )
    } catch (erreur) {
      if ((erreur as Error).name === "AbortError") return
      this.#annoncer(
        "Les lieux n'ont pas pu être chargés. Déplacez la carte pour réessayer.",
      )
    }
  }

  #urlDesLieux(): string {
    const zone = this.#zoneVisible()
    const parametres = new URLSearchParams({
      geste: this.gesteValue,
      bbox: JSON.stringify({
        southWest: { lng: zone.ouest, lat: zone.sud },
        northEast: { lng: zone.est, lat: zone.nord },
      }),
    })
    if (this.objetValue) parametres.set("objet", this.objetValue)
    return `${this.urlValue}?${parametres}`
  }

  #zoneVisible(): Zone {
    const bornes = this.carte!.getBounds()
    return {
      ouest: bornes.getWest(),
      sud: bornes.getSouth(),
      est: bornes.getEast(),
      nord: bornes.getNorth(),
    }
  }

  #dessiner() {
    const attendus = new Set(this.lieux.map((lieu) => lieu.uuid))

    this.marqueurs.forEach((marqueur, uuid) => {
      if (!attendus.has(uuid)) {
        marqueur.remove()
        this.marqueurs.delete(uuid)
      }
    })

    for (const lieu of this.lieux) {
      if (this.marqueurs.has(lieu.uuid)) continue

      const element = elementPinpoint(lieu, this.#couleurs(), this.gesteValue)
      element.addEventListener("click", () =>
        this.dispatch("lieuChoisi", { detail: { lieu } }),
      )

      const marqueur = new this.Marqueur({ element, anchor: "bottom" })
        .setLngLat([lieu.longitude, lieu.latitude])
        .addTo(this.carte!)
      this.marqueurs.set(lieu.uuid, marqueur)
    }
  }

  #couleurs(): CouleursPinpoint {
    const style = getComputedStyle(this.element)
    return {
      geste: style.getPropertyValue("--qfa-geste-couleur").trim(),
      bonus: style.getPropertyValue("--qfa-bonus-couleur").trim(),
      adresse: style.getPropertyValue("--qfa-adresse-usager").trim(),
    }
  }

  #masquerMarqueurs() {
    this.marqueurs.forEach((marqueur) => marqueur.remove())
    this.marqueurs.clear()
  }

  #annoncer(message: string) {
    if (this.hasMessageTarget) this.messageTarget.textContent = message
  }
}
