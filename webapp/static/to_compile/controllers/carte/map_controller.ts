import { Controller } from "@hotwired/stimulus"
import debounce from "lodash/debounce"
import { removeHash } from "../../js/helpers"
import { SolutionMap } from "../../js/solution_map"
import { ActorLocation, DisplayedActeur } from "../../js/types"


export class Actor implements DisplayedActeur {
  uuid: string
  fillBackground: boolean
  location: ActorLocation
  icon: string
  iconFile: string
  couleur: string
  bonus: boolean
  reparer: boolean

  constructor(actorFields: DisplayedActeur) {
    this.uuid = actorFields.uuid
    this.location = actorFields.location
    this.icon = actorFields.icon
    this.iconFile = actorFields.iconFile
    this.fillBackground = actorFields.fillBackground
    this.couleur = actorFields.couleur
    this.bonus = actorFields.bonus
    this.reparer = actorFields.reparer
  }
}

class MapController extends Controller<HTMLElement> {
  actorsMap: SolutionMap
  static targets = [
    "acteur",
    "searchInZoneButton",
    "bbox",
    "mapContainer",
    "loadingIndicator",
  ]
  static values = {
    location: { type: Object, default: {} },
    initialZoom: Number,
    theme: { type: String, default: "carto-light" },
    acteurFrameId: { type: String, default: "" },
    filterParams: { type: String, default: "" },
    // When true, the controller fetches acteurs from the GeoJSON endpoint and
    // renders them as a MapLibre symbol layer (the new carte behavior). When
    // false, it keeps the legacy DOM-marker path used by the formulaire page.
    useGeojsonLayer: { type: Boolean, default: false },
    // INSEE citycode of the commune the user picked from the address
    // autocomplete. When non-empty, the controller refetches the polygon from
    // geo.api.gouv.fr and draws the search-area overlay.
    searchAreaCitycode: { type: String, default: "" },
    // Pre-resolved polygon bbox JSON, computed server-side from the cached
    // commune feature. Lets the controller fit the camera synchronously on
    // connect (avoiding the camera jolt when the polygon fetch lands later).
    searchAreaBbox: { type: String, default: "" },
  }
  declare readonly acteurTargets: Array<HTMLElement>
  declare readonly searchInZoneButtonTarget: HTMLButtonElement
  declare readonly hasSearchInZoneButtonTarget: boolean
  declare readonly bboxTarget: HTMLInputElement
  declare readonly mapContainerTarget: HTMLDivElement
  declare readonly hasBboxTarget: boolean
  declare readonly loadingIndicatorTarget: HTMLDivElement
  declare readonly hasLoadingIndicatorTarget: boolean
  declare readonly locationValue: object
  declare readonly initialZoomValue: number
  declare readonly themeValue: string
  declare readonly acteurFrameIdValue: string
  declare readonly filterParamsValue: string
  declare readonly useGeojsonLayerValue: boolean
  declare readonly searchAreaCitycodeValue: string
  declare readonly searchAreaBboxValue: string

  #inFlightFetches = 0
  #latestBbox?: {
    southWest: { lat: number; lng: number }
    northEast: { lat: number; lng: number }
  }
  // Loading-spinner reveal is delayed so fast fetches don't flicker the
  // indicator. Per the carte spec, the spinner must not appear before this
  // many ms of in-flight fetch.
  #loadingDelayMs = 250
  #loadingDelayTimer?: number

  connect() {
    this.actorsMap = new SolutionMap({
      selector: this.mapContainerTarget,
      location: this.locationValue,
      initialZoom: this.initialZoomValue,
      controller: this,
      theme: this.themeValue,
    })

    let initialBbox: { southWest: { lat: number; lng: number }; northEast: { lat: number; lng: number } } | undefined

    // The form's bounding_box field is prefix-namespaced (e.g.
    // `carte_map-bounding_box`) so a plain `?bounding_box=…` URL param doesn't
    // populate it. Fall back to reading the URL param directly when present —
    // both for shareable links and for the iframe embed scenarios.
    const urlBbox = new URLSearchParams(window.location.search).get("bounding_box")
    if (urlBbox) {
      try {
        initialBbox = JSON.parse(urlBbox)
      } catch {
        initialBbox = undefined
      }
    }

    if (!initialBbox && this.hasBboxTarget && this.bboxTarget.value !== "") {
      try {
        initialBbox = JSON.parse(this.bboxTarget.value)
      } catch {
        initialBbox = undefined
      }
    }

    // Prefer the server-supplied search-area bbox when present: it's the
    // exact polygon extent of the commune the user selected, so the camera
    // lands on the right viewport synchronously (no jolt when the async
    // polygon fetch lands later).
    if (!initialBbox && this.searchAreaBboxValue) {
      try {
        initialBbox = JSON.parse(this.searchAreaBboxValue)
      } catch {
        initialBbox = undefined
      }
    }

    // After an address-search submit the server returns lat/lng but no bbox
    // (the queryset uses `from_center` for distance filtering). Without this
    // fallback the map would fall through to the camera default (zoom-3
    // whole-France) and the GeoJSON fetch would target a worldwide bbox.
    // Build a tight 300 m box around the searched location — natural framing
    // for a specific address (street / housenumber / locality). For
    // municipality-type results we already have a polygon bbox above.
    if (!initialBbox) {
      const loc = this.locationValue as { latitude?: number | string; longitude?: number | string }
      const lat = parseFloat(String(loc?.latitude ?? ""))
      const lng = parseFloat(String(loc?.longitude ?? ""))
      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        // 300 m radius. 1 deg lat ≈ 111 km everywhere; 1 deg lng ≈ cos(lat) *
        // 111 km, so we scale the longitude offset by 1 / cos(lat) to keep
        // the box visually square at metropolitan France latitudes.
        const radiusMeters = 300
        const halfLat = radiusMeters / 111_000
        const halfLng =
          radiusMeters / (111_000 * Math.cos((lat * Math.PI) / 180))
        initialBbox = {
          southWest: { lat: lat - halfLat, lng: lng - halfLng },
          northEast: { lat: lat + halfLat, lng: lng + halfLng },
        }
      }
    }

    // Detect a non-municipality address search: the user picked a street /
    // housenumber / locality (no citycode came back from the server) but we
    // do have lat/lng. In that case, switch to the KNN endpoint to fetch the
    // 30 nearest acteurs and fit the camera to their bbox — gives a useful
    // viewport even in sparse zones.
    const loc = this.locationValue as { latitude?: number | string; longitude?: number | string }
    const lat = parseFloat(String(loc?.latitude ?? ""))
    const lng = parseFloat(String(loc?.longitude ?? ""))
    const useKnn =
      !this.searchAreaCitycodeValue &&
      !this.searchAreaBboxValue &&
      Number.isFinite(lat) &&
      Number.isFinite(lng) &&
      // The URL bbox path is for shareable links / iframes; respect it over
      // the KNN heuristic.
      !new URLSearchParams(window.location.search).get("bounding_box")

    if (this.useGeojsonLayerValue) {
      // Defer to the next tick so MapLibre can finish setting up the canvas
      // before we register icons and add the layer.
      this.actorsMap.map.once("load", () => {
        if (useKnn) {
          void this.#fetchAndAppendNearest(lat, lng)
        } else {
          const bbox = initialBbox ?? this.#bboxFromCurrentView()
          void this.#fetchAndAppend(bbox, { fitBounds: !initialBbox })
        }
        // Re-fetch and draw the search-area overlay if a citycode survived
        // the Turbo Frame submit. Independent of the acteur fetch so the
        // overlay shows up even when the bbox is empty.
        if (this.searchAreaCitycodeValue) {
          void this.#applySearchArea(this.searchAreaCitycodeValue)
        }
      })

      if (initialBbox) {
        // Pre-zoom the map onto the requested bbox so the first fetch hits the
        // right area. Without this, the map starts centered on France and the
        // initial fetch returns features outside the chosen bbox. Animate so
        // a fresh address search reads as a smooth zoom rather than a jump.
        this.actorsMap.fitBounds([], initialBbox, { animate: true })
      }
    } else {
      // Legacy DOM-marker path used by formulaire.
      if (initialBbox) {
        this.actorsMap.addActorMarkersToMap(this.acteurTargets, initialBbox)
      } else {
        this.actorsMap.addActorMarkersToMap(this.acteurTargets)
      }
    }

    this.actorsMap.initEventListener()
    removeHash()
  }

  #bboxFromCurrentView() {
    const bounds = this.actorsMap.map.getBounds()
    return {
      southWest: { lng: bounds.getWest(), lat: bounds.getSouth() },
      northEast: { lng: bounds.getEast(), lat: bounds.getNorth() },
    }
  }

  // Refetch the commune polygon for the current citycode and draw it as the
  // search-area overlay outline. The camera was already fitted synchronously
  // on `connect()` using the server-supplied bbox, so this is purely a
  // visual enhancement that lands silently. Failures are swallowed: the
  // overlay is a UI nicety, not load-bearing.
  async #applySearchArea(citycode: string): Promise<void> {
    try {
      // Hit our same-origin proxy instead of geo.api.gouv.fr directly. The
      // server caches polygons for a year, so subsequent loads of the same
      // commune skip the upstream call entirely.
      const response = await fetch(`/carte/communes/${citycode}.geojson`)
      if (!response.ok) return
      const feature = await response.json()
      this.actorsMap.setSearchArea(feature)
    } catch (err) {
      console.error("commune polygon refetch failed", err)
    }
  }

  disconnect() {
    // Carte spec "Known fixes required" §3.4: abort any in-flight GeoJSON
    // fetch before tearing down the map, otherwise the fetch outlives the
    // controller and may try to mutate a removed source.
    this.actorsMap?.abortPendingFetch?.()
    this.actorsMap?.map?.remove()
  }

  initialize() {
    this.mapChanged = debounce(this.mapChanged, 300).bind(this)
  }

  mapChanged(event: CustomEvent) {
    this.dispatch("updateBbox", { detail: event.detail })

    // Per the carte spec, panning/zooming does not auto-fetch. Surface the
    // "Rechercher dans cette zone" button instead so the user explicitly
    // decides when to query the new area. Cached bbox is read on click.
    this.#latestBbox = {
      southWest: {
        lng: event.detail.southWest.lng,
        lat: event.detail.southWest.lat,
      },
      northEast: {
        lng: event.detail.northEast.lng,
        lat: event.detail.northEast.lat,
      },
    }
    this.#displaySearchInZoneButton()
  }

  // Stimulus action: fired when the user clicks "Rechercher dans cette zone".
  // Fetches acteurs for the latest known map bbox and appends them to the
  // GeoJSON layer (existing markers stay).
  searchInZone(event?: Event): void {
    event?.preventDefault()
    if (!this.useGeojsonLayerValue) {
      // Legacy formulaire path keeps its full-form submission (handled by
      // the state controller via the original data-action). This branch
      // shouldn't fire on the carte but is defensive.
      return
    }
    const bbox = this.#latestBbox ?? this.#bboxFromCurrentView()
    this.#hideSearchInZoneButton()
    void this.#fetchAndAppend(bbox, { fitBounds: false })
  }

  #displaySearchInZoneButton() {
    if (this.hasSearchInZoneButtonTarget) {
      this.searchInZoneButtonTarget.classList.remove("qf-hidden")
    }
  }

  #hideSearchInZoneButton() {
    if (this.hasSearchInZoneButtonTarget) {
      this.searchInZoneButtonTarget.classList.add("qf-hidden")
    }
  }

  async #fetchAndAppend(
    bbox: {
      southWest: { lat: number; lng: number }
      northEast: { lat: number; lng: number }
    },
    options: { fitBounds?: boolean } = {},
  ): Promise<void> {
    this.#showLoading(true)
    try {
      await this.actorsMap.loadActeursForBbox(bbox, {
        wipe: false,
        fitBounds: options.fitBounds,
        extraParams: this.filterParamsValue || undefined,
      })
    } finally {
      this.#showLoading(false)
    }
  }

  // KNN counterpart of #fetchAndAppend: hits the nearest-acteurs endpoint and
  // fits the camera to the returned features' bbox. Used on the initial load
  // after a non-municipality address search.
  async #fetchAndAppendNearest(lat: number, lng: number): Promise<void> {
    this.#showLoading(true)
    try {
      await this.actorsMap.loadActeursNearest(lat, lng, {
        count: 30,
        extraParams: this.filterParamsValue || undefined,
      })
    } finally {
      this.#showLoading(false)
    }
  }

  #showLoading(showing: boolean): void {
    if (showing) {
      this.#inFlightFetches += 1
    } else if (this.#inFlightFetches > 0) {
      this.#inFlightFetches -= 1
    }
    if (!this.hasLoadingIndicatorTarget) return

    if (this.#inFlightFetches > 0) {
      // Defer the actual reveal so a sub-250ms fetch never flickers the
      // spinner. If the fetch resolves first, the timer is cleared in the
      // else-branch below before it ever fires.
      if (!this.#loadingDelayTimer) {
        this.#loadingDelayTimer = window.setTimeout(() => {
          this.loadingIndicatorTarget.classList.remove("qf-hidden")
          this.#loadingDelayTimer = undefined
        }, this.#loadingDelayMs)
      }
    } else {
      if (this.#loadingDelayTimer) {
        window.clearTimeout(this.#loadingDelayTimer)
        this.#loadingDelayTimer = undefined
      }
      this.loadingIndicatorTarget.classList.add("qf-hidden")
    }
  }
}
export default MapController
