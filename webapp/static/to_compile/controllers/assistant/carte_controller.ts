import { Controller } from "@hotwired/stimulus"
import { useDebounce, useResize } from "stimulus-use"

import {
  merge,
  placesFromGeoJSON,
  type Area,
  type Place,
} from "../../js/assistant/visible_places"
import {
  addressElement,
  pinpointElement,
  type PinpointColors,
} from "../../js/assistant/pinpoint"
import type { Map as MapLibreMap, Marker, StyleSpecification } from "maplibre-gl"

type Timing = { server: number; total: number; places: number }

/** Reads `acteurs;dur=12.3` from the Server-Timing header. */
function serverDuration(header: string | null): number {
  const match = header?.match(/acteurs;dur=([\d.]+)/)
  return match ? Number(match[1]) : 0
}

/** Placeholder replaced by the place uuid in the URL pattern given by the template. */
const UUID_PLACEHOLDER = "__uuid__"

const SETTLE_DELAY_MS = 1000
const MIN_ZOOM = 9

export default class extends Controller<HTMLElement> {
  static targets = ["container", "message"]
  static values = {
    url: String,
    geste: String,
    objet: String,
    lieuUrl: String,
    workerUrl: String,
    longitude: Number,
    latitude: Number,
    preciseAddress: Boolean,
  }
  static outlets = ["assistant-chrono"]
  static debounces = [{ name: "refresh", wait: SETTLE_DELAY_MS }]

  declare readonly assistantChronoOutlets: { record(timing: Timing): void }[]
  declare readonly containerTarget: HTMLElement
  declare readonly messageTarget: HTMLElement
  declare readonly hasMessageTarget: boolean
  declare urlValue: string
  declare gesteValue: string
  declare objetValue: string
  declare lieuUrlValue: string
  declare workerUrlValue: string
  declare longitudeValue: number
  declare latitudeValue: number
  declare preciseAddressValue: boolean

  private map: MapLibreMap | null = null
  private MarkerClass!: typeof Marker
  private markers = new Map<string, Marker>()
  private places: Place[] = []
  private pendingRequest: AbortController | null = null

  async connect() {
    useDebounce(this)
    useResize(this)

    const [{ Map, Marker, NavigationControl, setWorkerUrl }, { mapStyles }] =
      await Promise.all([import("maplibre-gl"), import("carte-facile")])
    // Disconnected while the imports were loading (lookbook re-render): a map
    // created now would live on a detached node, and its worker and WebGL
    // context would never be released.
    if (!this.element.isConnected) return
    this.MarkerClass = Marker

    // Without an explicit URL the MapLibre worker never starts and the map
    // stays grey: see `static/to_compile/maplibre-worker.ts`.
    setWorkerUrl(this.workerUrlValue)

    this.map = new Map({
      container: this.containerTarget,
      // `carte-facile` ships its own copy of maplibre-gl (5.x) while V1
      // requires 6.x: the two `StyleSpecification` declarations diverge on an
      // optional field, `font-faces`. The object is identical at runtime; only
      // the declarations disagree, hence this deliberately narrow cast rather
      // than an `any`.
      style: mapStyles.desaturated as unknown as StyleSpecification,
      center: [this.longitudeValue, this.latitudeValue],
      zoom: 13,
      attributionControl: { compact: true },
    })
    this.map.addControl(new NavigationControl({ showCompass: false }), "top-left")

    // MapLibre measures its container at construction, before the stylesheet
    // is necessarily applied. Without this resize, the computed visible area
    // is that of a too-tall container and the fetched places land off-screen.
    this.map.resize()

    // Places are requested right away, without waiting for `load`.
    //
    // `load` only fires once the style *and* the first tiles are ready, close
    // to two seconds here. The request only needs the view bounds, known from
    // construction: the wait bought nothing. Both loads now progress together,
    // and the pins show up with the basemap instead of after it.
    const places = this.#load()

    // The address marker depends on no map data: placing it before `load`
    // spares it the wait for the tiles.
    this.#placeAddressMarker()

    await this.map.once("load")

    // `moveend` is only wired after `load`: the resize and the style setup
    // emit it, which would trigger a second load identical to the first.
    this.map.on("moveend", () => this.refresh())
    await places
  }

  /**
   * Red marker of the entered address.
   *
   * Placed once, never moved afterwards (#3356 §4): it marks where the user
   * said they are, not the current map center. Absent for a municipality,
   * which has no position to show: the geographic center of "Lyon" would
   * mislead.
   */
  #placeAddressMarker() {
    if (!this.map || !this.preciseAddressValue) return

    new this.MarkerClass({ element: addressElement(this.#colors()), anchor: "center" })
      .setLngLat([this.longitudeValue, this.latitudeValue])
      .addTo(this.map)
  }

  disconnect() {
    this.pendingRequest?.abort()
    this.markers.forEach((marker) => marker.remove())
    this.markers.clear()
    this.map?.remove()
    this.map = null
  }

  resize() {
    this.map?.resize()
  }

  /** Debounced: called on every `moveend`, only acts once the map is still. */
  refresh() {
    void this.#load()
  }

  async #load() {
    if (!this.map) return

    if (this.map.getZoom() < MIN_ZOOM) {
      this.#hideMarkers()
      this.#announce(
        "Zoomez sur la carte et faites-la défiler, ou cherchez une nouvelle adresse pour voir apparaître des points.",
      )
      return
    }

    this.pendingRequest?.abort()
    this.pendingRequest = new AbortController()

    const start = performance.now()
    try {
      const response = await fetch(this.#placesUrl(), {
        signal: this.pendingRequest.signal,
      })
      if (!response.ok) throw new Error(`response ${response.status}`)

      const incoming = placesFromGeoJSON(await response.json())
      const timing = {
        server: serverDuration(response.headers.get("Server-Timing")),
        total: performance.now() - start,
        places: incoming.length,
      }
      this.assistantChronoOutlets.forEach((chrono) => chrono.record(timing))
      this.places = merge(this.places, incoming, this.#visibleArea())
      this.#draw()
      this.#announce(
        this.places.length
          ? ""
          : "Aucun lieu trouvé ici. Déplacez la carte pour explorer une autre zone.",
      )
    } catch (error) {
      if ((error as Error).name === "AbortError") return
      this.#announce(
        "Les lieux n'ont pas pu être chargés. Déplacez la carte pour réessayer.",
      )
    }
  }

  #placesUrl(): string {
    const area = this.#visibleArea()
    const params = new URLSearchParams({
      geste: this.gesteValue,
      bbox: JSON.stringify({
        southWest: { lng: area.west, lat: area.south },
        northEast: { lng: area.east, lat: area.north },
      }),
    })
    if (this.objetValue) params.set("objet", this.objetValue)
    return `${this.urlValue}?${params}`
  }

  #visibleArea(): Area {
    const bounds = this.map!.getBounds()
    return {
      west: bounds.getWest(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      north: bounds.getNorth(),
    }
  }

  #draw() {
    const expected = new Set(this.places.map((place) => place.uuid))

    this.markers.forEach((marker, uuid) => {
      if (!expected.has(uuid)) {
        marker.remove()
        this.markers.delete(uuid)
      }
    })

    const colors = this.#colors()
    const lieuUrl = this.#lieuUrlBuilder()
    for (const place of this.places) {
      if (this.markers.has(place.uuid)) continue

      const element = pinpointElement(place, colors, this.gesteValue, lieuUrl)
      const marker = new this.MarkerClass({ element, anchor: "bottom" })
        .setLngLat([place.longitude, place.latitude])
        .addTo(this.map!)
      this.markers.set(place.uuid, marker)
    }
  }

  /**
   * Builder of the URL to a place's page, or nothing if the template gave
   * none: until that page exists, the pins stay buttons rather than links to
   * nowhere.
   */
  #lieuUrlBuilder(): ((uuid: string) => string) | undefined {
    if (!this.lieuUrlValue) return undefined
    return (uuid) => this.lieuUrlValue.replace(UUID_PLACEHOLDER, uuid)
  }

  #colors(): PinpointColors {
    const style = getComputedStyle(this.element)
    return {
      geste: style.getPropertyValue("--qfa-geste-color").trim(),
      bonus: style.getPropertyValue("--qfa-bonus-color").trim(),
      address: style.getPropertyValue("--qfa-user-address").trim(),
    }
  }

  #hideMarkers() {
    this.markers.forEach((marker) => marker.remove())
    this.markers.clear()
  }

  #announce(message: string) {
    if (this.hasMessageTarget) this.messageTarget.textContent = message
  }
}
