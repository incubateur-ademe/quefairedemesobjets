import { Controller } from "@hotwired/stimulus"

import {
  isInArea,
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

/**
 * What survives a screen change.
 *
 * The canvas is a Turbo permanent element (`layout/assistant.html`): the same
 * node travels from page to page, and with it the MapLibre instance, its
 * tiles, and the pins. This state hangs on the node so that the controller of
 * the next solutions screen picks it up instead of building a new map.
 */
type PersistedMap = {
  map: MapLibreMap
  Marker: typeof Marker
  markers: Map<string, Marker>
  places: Place[]
  addressMarker: Marker | null
  /** Gestes + objet: when they change, the pins are wrong and start over. */
  key: string
  /** Address the map was centered on: the view only moves when it changes. */
  address: [number, number]
  /** Last viewport requested: the same one is never asked twice in a row. */
  lastRequestedUrl: string
  onMoveEnd: (() => void) | null
}

const CANVAS_ID = "assistant-carte-canvas"

/** Reads `acteurs;dur=12.3` from the Server-Timing header. */
function serverDuration(header: string | null): number {
  const match = header?.match(/acteurs;dur=([\d.]+)/)
  return match ? Number(match[1]) : 0
}

/** Placeholder replaced by the place uuid in the URL pattern given by the template. */
const UUID_PLACEHOLDER = "__uuid__"

const MIN_ZOOM = 9
const INITIAL_ZOOM = 13
/** Matches the fade of `.qfa-pinpoint--leaving` in the stylesheet. */
const LEAVE_MS = 200

export default class extends Controller<HTMLElement> {
  static targets = ["message", "messageText"]
  static values = {
    url: String,
    geste: String,
    fiche: String,
    lieuUrl: String,
    workerUrl: String,
    longitude: Number,
    latitude: Number,
    preciseAddress: Boolean,
  }
  static outlets = ["assistant-chrono"]

  declare readonly assistantChronoOutlets: { record(timing: Timing): void }[]
  declare readonly messageTarget: HTMLElement
  declare readonly hasMessageTarget: boolean
  declare readonly messageTextTarget: HTMLElement
  declare urlValue: string
  declare gesteValue: string
  declare ficheValue: string
  declare lieuUrlValue: string
  declare workerUrlValue: string
  declare longitudeValue: number
  declare latitudeValue: number
  declare preciseAddressValue: boolean

  private state: PersistedMap | null = null
  private pendingRequest: AbortController | null = null

  async connect() {
    const canvas = await this.#canvasOnceRendered()
    if (!canvas) return

    const existing = (canvas as HTMLElement & { assistantMap?: PersistedMap })
      .assistantMap
    const state = existing ?? (await this.#createMap(canvas))
    // Disconnected while the map was being created (a second render of the
    // same screen): the next instance owns the canvas, this one steps aside.
    if (!state || !this.element.isConnected) return
    this.state = state
    ;(canvas as HTMLElement & { assistantMap?: PersistedMap }).assistantMap = state

    if (existing) this.#reuse(existing)

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

    if (!existing) {
      await state.map.once("load")
      // `disconnect()` may have run during the wait: it cleared `this.state`.
      if (this.state !== state) return
      // MapLibre opens the compact attribution on load; the mockup shows it
      // folded (30141:9028). It stays openable by the user.
      canvas
        .querySelector(".maplibregl-ctrl-attrib")
        ?.classList.remove("maplibregl-compact-show")
    }

    // `moveend` is only wired after `load`: the resize and the style setup
    // emit it, which would trigger a second load identical to the first.
    state.onMoveEnd = () => this.refresh()
    state.map.on("moveend", state.onMoveEnd)
    await places
  }

  async #createMap(canvas: HTMLElement): Promise<PersistedMap | null> {
    const [{ Map: MapLibre, Marker, NavigationControl, setWorkerUrl }, { mapStyles }] =
      await Promise.all([import("maplibre-gl"), import("carte-facile")])
    // Disconnected while the imports were loading (lookbook re-render): a map
    // created now would live on a detached node, and its worker and WebGL
    // context would never be released.
    if (!this.element.isConnected) return null

    // Without an explicit URL the MapLibre worker never starts and the map
    // stays grey: see `static/to_compile/maplibre-worker.ts`.
    setWorkerUrl(this.workerUrlValue)

    const map = new MapLibre({
      container: canvas,
      // `carte-facile` ships its own copy of maplibre-gl (5.x) while V1
      // requires 6.x: the two `StyleSpecification` declarations diverge on an
      // optional field, `font-faces`. The object is identical at runtime; only
      // the declarations disagree, hence this deliberately narrow cast rather
      // than an `any`.
      style: mapStyles.desaturated as unknown as StyleSpecification,
      center: [this.longitudeValue, this.latitudeValue],
      zoom: INITIAL_ZOOM,
      attributionControl: { compact: true },
    })
    map.addControl(new NavigationControl({ showCompass: false }), "top-left")

    // MapLibre measures its container at construction, before the stylesheet
    // is necessarily applied. Without this resize, the computed visible area
    // is that of a too-tall container and the fetched places land off-screen.
    map.resize()

    return {
      map,
      Marker,
      markers: new Map(),
      places: [],
      addressMarker: null,
      key: this.#key(),
      address: [this.longitudeValue, this.latitudeValue],
      lastRequestedUrl: "",
      onMoveEnd: null,
    }
  }

  /**
   * The map came back from another screen. It was parked hidden, so its size
   * is stale; the search may have changed too.
   */
  #reuse(state: PersistedMap) {
    if (state.onMoveEnd) state.map.off("moveend", state.onMoveEnd)
    state.map.resize()

    // Another geste or objet: the pins on screen answer the previous search.
    if (state.key !== this.#key()) {
      state.markers.forEach((marker) => marker.remove())
      state.markers.clear()
      state.places = []
      state.key = this.#key()
    }

    // Another address: recenter as a first display would. The same address
    // keeps the view where the user left it, pans and zooms included: the
    // spec forbids any automatic recentering after the first display (#3356).
    const [lng, lat] = state.address
    const addressChanged =
      Math.abs(lng - this.longitudeValue) > 1e-6 ||
      Math.abs(lat - this.latitudeValue) > 1e-6
    if (addressChanged) {
      state.address = [this.longitudeValue, this.latitudeValue]
      state.map.jumpTo({
        center: [this.longitudeValue, this.latitudeValue],
        zoom: INITIAL_ZOOM,
      })
    }
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
    if (!this.state) return
    this.state.addressMarker?.remove()
    this.state.addressMarker = null
    if (!this.preciseAddressValue) return

    this.state.addressMarker = new this.state.Marker({
      element: addressElement(this.#colors()),
      anchor: "center",
      subpixelPositioning: true,
    })
      .setLngLat([this.longitudeValue, this.latitudeValue])
      .addTo(this.state.map)
  }

  disconnect() {
    this.pendingRequest?.abort()
    const state = this.state
    const canvas = this.#canvas()
    this.state = null
    if (!state) return

    if (state.onMoveEnd) state.map.off("moveend", state.onMoveEnd)
    state.onMoveEnd = null

    // Turbo moves the permanent canvas to the next screen synchronously; only
    // when it is truly gone (lookbook re-render, document torn down) must the
    // WebGL context be released. Decide once the DOM has settled.
    setTimeout(() => {
      if (canvas?.isConnected) return
      state.markers.forEach((marker) => marker.remove())
      state.addressMarker?.remove()
      state.map.remove()
      if (canvas)
        delete (canvas as HTMLElement & { assistantMap?: PersistedMap }).assistantMap
    })
  }

  /**
   * Called on every `moveend`. No debounce: MapLibre only emits it once the
   * gesture is over, and a request still in flight is aborted by the next one.
   */
  refresh() {
    void this.#load()
  }

  async #load() {
    const state = this.state
    const canvas = this.#canvas()
    if (!state || !canvas) return
    // Parked behind another screen: MapLibre reports a collapsed viewport,
    // and nothing is worth fetching for it. Showing it again re-emits
    // `moveend` with the real bounds.
    if (!canvas.clientWidth) return

    // Below the département zoom, the pins are hidden by CSS but kept in the
    // DOM and in memory: zooming back in shows them at once, without waiting
    // for a request, and nothing is rebuilt. Toggling a class rather than
    // removing markers also keeps the canvas size constant, so MapLibre has
    // nothing to re-render (#3356).
    const zoomedOut = state.map.getZoom() < MIN_ZOOM
    this.element.dataset.zoomedOut = String(zoomedOut)
    if (zoomedOut) {
      this.#announce(
        "Zoomez sur la carte et faites-la défiler, ou cherchez une nouvelle adresse pour voir apparaître des points.",
      )
      return
    }

    // Whatever memory holds is drawn before asking the server: the map is
    // never empty while a request is in flight.
    this.#draw()

    // MapLibre also emits `moveend` on a container resize, even when the view
    // did not move: the same viewport is never requested twice in a row.
    const url = this.#placesUrl()
    if (url === state.lastRequestedUrl) return
    state.lastRequestedUrl = url

    this.pendingRequest?.abort()
    this.pendingRequest = new AbortController()

    const start = performance.now()
    try {
      const response = await fetch(url, {
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
      const area = this.#visibleArea()
      state.places = merge(state.places, incoming, area)
      this.#draw()
      this.#announce(
        state.places.some((place) => isInArea(place, area))
          ? ""
          : "Aucun lieu trouvé ici. Déplacez la carte pour explorer une autre zone.",
      )
    } catch (error) {
      if ((error as Error).name === "AbortError") return
      // Let the next move retry the same viewport.
      state.lastRequestedUrl = ""
      this.#announce(
        "Les lieux n'ont pas pu être chargés. Déplacez la carte pour réessayer.",
      )
    }
  }

  #placesUrl(): string {
    const area = this.#visibleArea()
    const params = new URLSearchParams({
      bbox: JSON.stringify({
        southWest: { lng: area.west, lat: area.south },
        northEast: { lng: area.east, lat: area.north },
      }),
    })
    // One `geste` per code: a block of the fiche may span two gestes.
    for (const code of this.#gestes()) params.append("geste", code)
    if (this.ficheValue) params.set("fiche", this.ficheValue)
    return `${this.urlValue}?${params}`
  }

  #visibleArea(): Area {
    const bounds = this.state!.map.getBounds()
    return {
      west: bounds.getWest(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      north: bounds.getNorth(),
    }
  }

  #draw() {
    const state = this.state
    if (!state) return
    const expected = new Set(state.places.map((place) => place.uuid))

    state.markers.forEach((marker, uuid) => {
      if (!expected.has(uuid)) {
        // Fade out before leaving the DOM (see `.qfa-pinpoint--leaving`).
        marker.getElement().classList.add("qfa-pinpoint--leaving")
        setTimeout(() => marker.remove(), LEAVE_MS)
        state.markers.delete(uuid)
      }
    })

    const colors = this.#colors()
    const lieuUrl = this.#lieuUrlBuilder()
    for (const place of state.places) {
      if (state.markers.has(place.uuid)) continue

      // The pin shows the icon of the block's first geste.
      const element = pinpointElement(place, colors, this.#gestes()[0] ?? "", lieuUrl)
      const marker = new state.Marker({
        element,
        anchor: "bottom",
        // Without it MapLibre rounds marker positions to whole pixels, which
        // makes the pins jitter during zoom animations.
        subpixelPositioning: true,
      })
        .setLngLat([place.longitude, place.latitude])
        .addTo(state.map)
      state.markers.set(place.uuid, marker)
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

  #gestes(): string[] {
    return this.gesteValue.split(",").filter(Boolean)
  }

  #key(): string {
    return `${this.gesteValue}|${this.objetValue}`
  }

  /** The permanent canvas, by id: the node may come from another page's parking. */
  #canvas(): HTMLElement | null {
    return this.element.querySelector<HTMLElement>(`#${CANVAS_ID}`)
  }

  /**
   * During a Turbo Drive render, Stimulus connects this controller while the
   * permanent canvas is still a placeholder: Turbo swaps the body, awaits a
   * repaint, then puts the permanent elements back. The canvas is therefore
   * looked up again once the visit has rendered.
   */
  async #canvasOnceRendered(): Promise<HTMLElement | null> {
    const found = this.#canvas()
    if (found) return found
    await new Promise<void>((resolve) => {
      const done = () => {
        clearTimeout(timer)
        resolve()
      }
      const timer = setTimeout(done, 2000)
      document.addEventListener("turbo:load", done, { once: true })
    })
    return this.#canvas()
  }

  #colors(): PinpointColors {
    const style = getComputedStyle(this.element)
    return {
      geste: style.getPropertyValue("--qfa-geste-color").trim(),
      bonus: style.getPropertyValue("--qfa-bonus-color").trim(),
      address: style.getPropertyValue("--qfa-user-address").trim(),
    }
  }

  #announce(message: string) {
    if (!this.hasMessageTarget) return
    this.messageTextTarget.textContent = message
    this.messageTarget.hidden = !message
  }
}
