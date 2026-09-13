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
  static debounces = [{ name: "rafraichir", wait: DELAI_STABILISATION_MS }]

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
    this.carte.on("moveend", () => this.rafraichir())
    this.carte.on("load", () => this.rafraichir())
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

  async rafraichir() {
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

    try {
      const reponse = await fetch(this.#urlDesLieux(), {
        signal: this.requeteEnCours.signal,
      })
      if (!reponse.ok) throw new Error(`réponse ${reponse.status}`)

      const nouveaux = lieuxDepuisGeoJSON(await reponse.json())
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

      const element = elementPinpoint(lieu, this.#couleurs())
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
