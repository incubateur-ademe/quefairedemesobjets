import { Controller } from "@hotwired/stimulus"
import { useDebounce, useResize } from "stimulus-use"

import {
  fusionner,
  lieuxDepuisGeoJSON,
  type Lieu,
  type Zone,
} from "../../js/assistant/lieux_visibles"
import {
  elementAdresse,
  elementPinpoint,
  type CouleursPinpoint,
} from "../../js/assistant/pinpoint"
import type { Map as CarteMapLibre, Marker, StyleSpecification } from "maplibre-gl"

type Mesure = { serveur: number; total: number; lieux: number }

/** Lit `acteurs;dur=12.3` dans l'en-tête Server-Timing. */
function dureeServeur(entete: string | null): number {
  const correspondance = entete?.match(/acteurs;dur=([\d.]+)/)
  return correspondance ? Number(correspondance[1]) : 0
}

/** Marque remplacée par l'uuid du lieu dans l'URL modèle fournie par le gabarit. */
const GABARIT_UUID = "__uuid__"

const DELAI_STABILISATION_MS = 1000
const ZOOM_MINIMUM = 9

export default class extends Controller<HTMLElement> {
  static targets = ["conteneur", "message"]
  static values = {
    url: String,
    geste: String,
    objet: String,
    urlLieu: String,
    longitude: Number,
    latitude: Number,
    adressePrecise: Boolean,
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
  declare urlLieuValue: string
  declare longitudeValue: number
  declare latitudeValue: number
  declare adressePreciseValue: boolean

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
      // `carte-facile` embarque sa propre copie de maplibre-gl (5.x) alors que
      // la V1 en exige une 6.x : les deux déclarations de `StyleSpecification`
      // divergent sur un champ optionnel, `font-faces`. L'objet est identique à
      // l'exécution ; seules les déclarations se contredisent, d'où ce cast
      // délibérément étroit plutôt qu'un `any`.
      style: mapStyles.desaturated as unknown as StyleSpecification,
      center: [this.longitudeValue, this.latitudeValue],
      zoom: 13,
      attributionControl: { compact: true },
    })
    this.carte.addControl(new NavigationControl({ showCompass: false }), "top-left")

    // MapLibre mesure son conteneur à la construction, avant que la feuille de
    // styles ne soit forcément appliquée. Sans ce resize, la zone visible
    // calculée est celle d'un conteneur trop haut et les lieux ramenés tombent
    // hors de l'écran.
    this.carte.resize()

    // Les lieux sont demandés tout de suite, sans attendre `load`.
    //
    // `load` n'est émis qu'une fois le style *et* les premières tuiles prêtes,
    // soit près de deux secondes ici. Or la requête n'a besoin que des bornes
    // de la vue, connues dès la construction : l'attente était gratuite. Les
    // deux chargements avancent désormais de front, et les punaises
    // apparaissent avec le fond de carte au lieu de le suivre.
    const lieux = this.#charger()

    // La punaise de l'adresse ne dépend d'aucune donnée de carte : la poser
    // avant `load` évite de la faire attendre les tuiles.
    this.#poserAdresse()

    await this.carte.once("load")

    // L'écoute de `moveend` n'est branchée qu'après `load` : le resize et la
    // mise en place du style en émettent, qui déclencheraient un second
    // chargement identique au premier.
    this.carte.on("moveend", () => this.rafraichir())
    await lieux
  }

  /**
   * Punaise rouge de l'adresse saisie.
   *
   * Posée une seule fois, jamais déplacée ensuite (#3356 §4) : elle marque là
   * où l'usager a dit se trouver, pas le centre courant de la carte. Absente
   * pour une commune, qui n'a pas de position à montrer — le centre
   * géographique de « Lyon » induirait en erreur.
   */
  #poserAdresse() {
    if (!this.carte || !this.adressePreciseValue) return

    new this.Marqueur({ element: elementAdresse(this.#couleurs()), anchor: "center" })
      .setLngLat([this.longitudeValue, this.latitudeValue])
      .addTo(this.carte)
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

      const element = elementPinpoint(lieu, this.#couleurs(), this.gesteValue, (uuid) =>
        this.urlLieuValue.replace(GABARIT_UUID, uuid),
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
