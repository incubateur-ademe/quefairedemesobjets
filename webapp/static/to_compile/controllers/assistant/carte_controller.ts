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
import {
  CANVAS_ID,
  type CanvasWithMap,
  type PersistedMap,
} from "../../js/assistant/persisted_map"
import { serverDuration, type Timing } from "./chrono_controller"

const UUID_PLACEHOLDER = "__uuid__"

const MIN_ZOOM = 9
const INITIAL_ZOOM = 13
/** A single nearby place must not zoom down to the street. */
const FIT_MAX_ZOOM = 16
/** Pins are anchored at their bottom: the top needs room for their height. */
const FIT_PADDING = { top: 64, bottom: 32, left: 32, right: 32 }
/** Matches the fade of `.qfa-pinpoint--leaving` in the stylesheet. */
const LEAVE_MS = 200
const CANVAS_WAIT_MS = 2000

export default class extends Controller<HTMLElement> {
  static targets = ["message", "messageText"]
  static values = {
    url: String,
    geste: String,
    fiche: String,
    lieuUrl: String,
    workerUrl: String,
    styleUrl: String,
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
  declare styleUrlValue: string
  declare longitudeValue: number
  declare latitudeValue: number
  declare preciseAddressValue: boolean

  #state: PersistedMap | null = null
  #pendingRequest: AbortController | null = null

  async connect() {
    const canvas = await this.#canvasOnceRendered()
    if (!canvas) return

    const existing = canvas.assistantMap
    const state = existing ?? (await this.#createMap(canvas))
    // Disconnected while the map was being created: the next instance owns
    // the canvas.
    if (!state || !this.element.isConnected) return
    this.#state = state
    canvas.assistantMap = state

    if (existing) this.#reuse(existing)

    // Not waiting for `load` (style and first tiles): the request only needs
    // the view bounds, so the pins arrive with the basemap.
    const places = this.#load()
    this.#placeAddressMarker()

    if (!existing) {
      await state.map.once("load")
      if (this.#state !== state) return
      // MapLibre opens the compact attribution on load; keep it folded.
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

  async #createMap(canvas: CanvasWithMap): Promise<PersistedMap | null> {
    const {
      Map: MapLibre,
      Marker,
      NavigationControl,
      setWorkerUrl,
    } = await import("maplibre-gl")
    // A map created on a detached node would never release its WebGL context.
    if (!this.element.isConnected) return null

    // Without an explicit URL the bundled worker never starts and the map
    // stays grey (`maplibre-worker.ts`).
    setWorkerUrl(this.workerUrlValue)

    const map = new MapLibre({
      container: canvas,
      style: this.styleUrlValue,
      center: [this.longitudeValue, this.latitudeValue],
      zoom: INITIAL_ZOOM,
      attributionControl: { compact: true },
    })
    map.addControl(new NavigationControl({ showCompass: false }), "top-left")

    // Measured at construction, possibly before the stylesheet applies: the
    // visible area would be too tall and the places would land off-screen.
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
      needsFit: true,
      onMoveEnd: null,
    }
  }

  /** The map came back from another screen: stale size, maybe another search. */
  #reuse(state: PersistedMap) {
    if (state.onMoveEnd) state.map.off("moveend", state.onMoveEnd)
    state.map.resize()

    if (state.key !== this.#key()) {
      this.#forgetPlaces(state)
      state.key = this.#key()
    }

    // A new address is a new search; otherwise the view and its pins stay
    // where the user left them.
    const [lng, lat] = state.address
    const addressChanged =
      Math.abs(lng - this.longitudeValue) > 1e-6 ||
      Math.abs(lat - this.latitudeValue) > 1e-6
    if (addressChanged) {
      this.#forgetPlaces(state)
      state.address = [this.longitudeValue, this.latitudeValue]
      state.needsFit = true
      state.map.jumpTo({
        center: [this.longitudeValue, this.latitudeValue],
        zoom: INITIAL_ZOOM,
      })
    }
  }

  #forgetPlaces(state: PersistedMap) {
    state.markers.forEach((marker) => marker.remove())
    state.markers.clear()
    state.places = []
  }

  /** Marker of the entered address; none for a municipality, which has no
   * position to show. */
  #placeAddressMarker() {
    if (!this.#state) return
    this.#state.addressMarker?.remove()
    this.#state.addressMarker = null
    if (!this.preciseAddressValue) return

    this.#state.addressMarker = new this.#state.Marker({
      element: addressElement(this.#colors()),
      anchor: "center",
      subpixelPositioning: true,
    })
      .setLngLat([this.longitudeValue, this.latitudeValue])
      .addTo(this.#state.map)
  }

  disconnect() {
    this.#pendingRequest?.abort()
    const state = this.#state
    const canvas = this.#canvas()
    this.#state = null
    if (!state) return

    if (state.onMoveEnd) state.map.off("moveend", state.onMoveEnd)
    state.onMoveEnd = null

    // Turbo moves the permanent canvas to the next screen synchronously: only
    // release the WebGL context once the DOM has settled without it.
    setTimeout(() => {
      if (canvas?.isConnected) return
      state.markers.forEach((marker) => marker.remove())
      state.addressMarker?.remove()
      state.map.remove()
      if (canvas) delete canvas.assistantMap
    })
  }

  /** On every `moveend`, emitted once the gesture is over. */
  refresh() {
    void this.#load()
  }

  async #load() {
    const state = this.#state
    const canvas = this.#canvas()
    if (!state || !canvas) return
    // Parked behind another screen: a collapsed viewport, nothing to fetch.
    if (!canvas.clientWidth) return

    // Zoomed out, the pins are hidden by CSS but kept: zooming back in shows
    // them at once.
    const zoomedOut = state.map.getZoom() < MIN_ZOOM
    this.element.dataset.zoomedOut = String(zoomedOut)
    if (zoomedOut) {
      this.#announce(
        "Zoomez sur la carte et faites-la défiler, ou cherchez une nouvelle adresse pour voir apparaître des points.",
      )
      return
    }

    this.#draw()

    // `moveend` also fires on a resize without any move.
    const url = this.#placesUrl()
    if (url === state.lastRequestedUrl) return
    state.lastRequestedUrl = url

    this.#pendingRequest?.abort()
    this.#pendingRequest = new AbortController()

    const start = performance.now()
    try {
      const response = await fetch(url, {
        signal: this.#pendingRequest.signal,
      })
      if (!response.ok) throw new Error(`response ${response.status}`)

      const incoming = placesFromGeoJSON(await response.json())
      const timing = {
        server: serverDuration(response.headers.get("Server-Timing")),
        total: performance.now() - start,
        places: incoming.length,
      }
      this.assistantChronoOutlets.forEach((chrono) => chrono.record(timing))
      // Framed first: the visible area is the one the user will see.
      this.#fitOnce(incoming)
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
      state.lastRequestedUrl = ""
      this.#announce(
        "Les lieux n'ont pas pu être chargés. Déplacez la carte pour réessayer.",
      )
    }
  }

  /** Frames the first places found around a new address, once. */
  #fitOnce(places: Place[]) {
    const state = this.#state
    if (!state?.needsFit) return
    state.needsFit = false
    if (places.length === 0) return

    const points: [number, number][] = places.map((place) => [
      place.longitude,
      place.latitude,
    ])
    if (this.preciseAddressValue) points.push(state.address)
    const lngs = points.map(([lng]) => lng)
    const lats = points.map(([, lat]) => lat)
    state.map.fitBounds(
      [
        [Math.min(...lngs), Math.min(...lats)],
        [Math.max(...lngs), Math.max(...lats)],
      ],
      { padding: FIT_PADDING, maxZoom: FIT_MAX_ZOOM, duration: 0 },
    )
  }

  #placesUrl(): string {
    const state = this.#state!
    const area = this.#visibleArea()
    // Around the address first, then the visible area.
    const params = state.needsFit
      ? new URLSearchParams({
          longitude: String(state.address[0]),
          latitude: String(state.address[1]),
        })
      : new URLSearchParams({
          bbox: JSON.stringify({
            southWest: { lng: area.west, lat: area.south },
            northEast: { lng: area.east, lat: area.north },
          }),
        })
    for (const code of this.#gestes()) params.append("geste", code)
    if (this.ficheValue) params.set("fiche", this.ficheValue)
    return `${this.urlValue}?${params}`
  }

  #visibleArea(): Area {
    const bounds = this.#state!.map.getBounds()
    return {
      west: bounds.getWest(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      north: bounds.getNorth(),
    }
  }

  #draw() {
    const state = this.#state
    if (!state) return
    const expected = new Set(state.places.map((place) => place.uuid))

    state.markers.forEach((marker, uuid) => {
      if (!expected.has(uuid)) {
        marker.getElement().classList.add("qfa-pinpoint--leaving")
        setTimeout(() => marker.remove(), LEAVE_MS)
        state.markers.delete(uuid)
      }
    })

    const colors = this.#colors()
    const lieuUrl = this.#lieuUrlBuilder()
    for (const place of state.places) {
      if (state.markers.has(place.uuid)) continue

      const geste = place.geste || (this.#gestes()[0] ?? "")
      const element = pinpointElement(place, colors, geste, lieuUrl)
      const marker = new state.Marker({
        element,
        anchor: "bottom",
        // Whole-pixel rounding makes pins jitter while zooming.
        subpixelPositioning: true,
      })
        .setLngLat([place.longitude, place.latitude])
        .addTo(state.map)
      state.markers.set(place.uuid, marker)
    }
  }

  #lieuUrlBuilder(): ((uuid: string) => string) | undefined {
    if (!this.lieuUrlValue) return undefined
    return (uuid) => this.lieuUrlValue.replace(UUID_PLACEHOLDER, uuid)
  }

  #gestes(): string[] {
    return this.gesteValue.split(",").filter(Boolean)
  }

  #key(): string {
    return `${this.gesteValue}|${this.ficheValue}`
  }

  #canvas(): CanvasWithMap | null {
    return this.element.querySelector<HTMLElement>(`#${CANVAS_ID}`)
  }

  /**
   * Stimulus connects during a Turbo render while the permanent canvas is
   * still a placeholder: look it up again once the visit has rendered.
   */
  async #canvasOnceRendered(): Promise<CanvasWithMap | null> {
    const found = this.#canvas()
    if (found) return found
    await new Promise<void>((resolve) => {
      const done = () => {
        clearTimeout(timer)
        document.removeEventListener("turbo:load", done)
        resolve()
      }
      const timer = setTimeout(done, CANVAS_WAIT_MS)
      document.addEventListener("turbo:load", done, { once: true })
    })
    return this.#canvas()
  }

  #colors(): PinpointColors {
    const style = getComputedStyle(this.element)
    return {
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
