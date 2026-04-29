import { addOverlay, mapStyles, Overlay } from "carte-facile"
import "carte-facile/dist/carte-facile.css"
import maplibregl, {
  FitBoundsOptions,
  GeoJSONSource,
  LngLat,
  LngLatBoundsLike,
  Map,
  Marker,
} from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import MapController from "../controllers/carte/map_controller"
import { registerActeurIcons } from "./acteur_icons"
import type { Location } from "./types"

const DEFAULT_LOCATION: LngLat = new LngLat(2.213749, 46.227638)
const DEFAULT_INITIAL_ZOOM: number = 5
const DEFAULT_MAX_ZOOM: number = 18

const ACTEURS_SOURCE_ID = "acteurs"
const ACTEURS_LAYER_ID = "acteurs-layer"
const GEOJSON_ENDPOINT = "/carte/acteurs.geojson"
const GEOJSON_NEAR_ENDPOINT = "/carte/acteurs-near.geojson"
// Search-area overlay: when the user picks a municipality from the address
// autocomplete, we draw the commune outline as a contextual cue. Source +
// line layer are added on first call to setSearchArea (no fill, just outline).
const SEARCH_AREA_SOURCE_ID = "search-area"
const SEARCH_AREA_LINE_LAYER_ID = "search-area-line"
const SEARCH_AREA_COLOR = "#e1000f" // DSFR red
// Carte spec §3.7: soft alarm fires once per session when the in-memory
// feature count crosses this threshold. Used as a telemetry signal to gate
// the LRU eviction feature flag.
const ACTEURS_SOFT_ALARM_THRESHOLD = 3000

type ActeurBbox = {
  southWest: { lng: number; lat: number }
  northEast: { lng: number; lat: number }
}

type ActeurFeature = {
  type: "Feature"
  geometry: { type: "Point"; coordinates: [number, number] }
  properties: {
    uuid: string
    icon: string
    bonus: boolean
    detail_url: string
  }
}

type GeoJsonResponse = {
  features: ActeurFeature[]
  // Top-level flag the backend emits when the result set hit the cap. The
  // controller surfaces this as a "zoom in to see more" pill.
  truncated?: boolean
}

export class SolutionMap {
  map: Map
  #location: Location
  #mapWidthBeforeResize: number
  #controller: MapController
  #useOsm: boolean
  bboxValue?: Array<Number>
  points: Array<Array<Number>>
  mapPadding: number = 50
  initialZoom: number = DEFAULT_INITIAL_ZOOM

  // Track the uuids currently rendered on the symbol layer so we can dedupe on
  // append and pass `exclude_uuids` to the backend when fetching more features.
  #displayedUuids: Set<string> = new Set()
  // Authoritative copy of the features currently rendered. We don't trust the
  // GeoJSONSource to expose its data back to us, so we keep our own.
  #displayedFeatures: ActeurFeature[] = []
  #iconsRegistered = false
  #acteursSourceReady = false
  #pendingFetchAbort?: AbortController
  // Set to true once the map's containing layout has stopped resizing and the
  // initial fit-bounds has run. After that, further re-fits are skipped so we
  // don't fight the user when they zoom or pan.
  #layoutSettled = false
  // Carte spec §3.7: soft-alarm telemetry fires once per session.
  #softAlarmFired = false

  constructor({
    selector,
    location,
    controller,
    initialZoom = DEFAULT_INITIAL_ZOOM,
    theme,
  }: {
    selector: HTMLDivElement
    location: Location
    controller: MapController
    initialZoom: number
    theme: string
  }) {
    this.#location = location
    this.#controller = controller

    // Use OSM tiles for Django admin, Carte Facile for public site
    this.#useOsm = theme === "osm"

    const osmStyle = {
      version: 8 as const,
      sources: {
        osm: {
          type: "raster" as const,
          tiles: [
            "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
          ],
          tileSize: 256,
        },
      },
      layers: [{ type: "raster" as const, id: "osm-layer", source: "osm" }],
    }

    this.map = new Map({
      container: selector,
      style: this.#useOsm ? osmStyle : mapStyles.desaturated,
      zoom: initialZoom,
      maxZoom: this.#useOsm ? DEFAULT_MAX_ZOOM : 18.9,
      center: DEFAULT_LOCATION,
      attributionControl: {
        compact: true,
        ...(this.#useOsm && { customAttribution: "© OpenStreetMap contributors" }),
      },
      // MapLibre's default fade animation cross-fades symbols when tiles
      // reload during a pan/zoom (~300 ms). With our small acteur dataset
      // that reads as a "flash" — pinpoints fade out and back in even when
      // the underlying data hasn't changed. Setting it to 0 removes the
      // visible reflow without affecting correctness.
      fadeDuration: 0,
    })

    if (!this.#useOsm) {
      addOverlay(this.map, Overlay.administrativeBoundaries)
    }
    // Add zoom controls
    this.#addZoomControl()

    if (
      this.#location.latitude !== undefined &&
      this.#location.longitude !== undefined
    ) {
      new maplibregl.Marker({
        element: this.#initialiseHomeMarker(),
      })
        .setLngLat([this.#location.longitude, this.#location.latitude])
        .setPopup(
          new maplibregl.Popup().setHTML("<p><strong>Vous êtes ici !</strong></p>"),
        )
        .addTo(this.map)
    }
  }

  #initialiseHomeMarker() {
    const homePinPoint = document.getElementById("pinpoint-home")
    if (!homePinPoint) {
      return null
    }

    // The home pin point is hidden by default
    // so that it does not display randomly behind the preview screen.
    homePinPoint.classList.remove("qf-invisible")
    return homePinPoint
  }

  addActorMarkersToMap(actors: Array<HTMLElement>, bboxValue?: Array<Number>): void {
    const points: Array<Array<Number>> = []
    actors.forEach(function (actor: HTMLElement) {
      const longitude = actor.dataset?.longitude
      const latitude = actor.dataset?.latitude
      const draggable = actor.dataset?.draggable === "true"

      if (longitude && latitude) {
        let longitudeFloat = parseFloat(longitude.replace(",", "."))
        let latitudeFloat = parseFloat(latitude.replace(",", "."))
        actor.classList.remove("qf-invisible")

        const marker: Marker = new maplibregl.Marker({
          element: actor,
          draggable: draggable,
        }).setLngLat([longitudeFloat, latitudeFloat])

        if (draggable) {
          this.#setupMarkerDragListener(marker)
        }

        marker.addTo(this.map)
        points.push([latitudeFloat, longitudeFloat])
      }
    }, this)
    this.fitBounds(points, bboxValue)
  }

  #setupMarkerDragListener(marker: Marker) {
    marker.on("dragend", () => {
      const lngLat = marker.getLngLat()
      this.#controller.dispatch("markerDragged", {
        detail: {
          latitude: lngLat.lat.toString(),
          longitude: lngLat.lng.toString(),
          markerElement: marker.getElement(),
        },
        bubbles: true,
        cancelable: false,
      })
    })
  }

  // Fetch acteurs in the given bbox from the JSON endpoint and append them to
  // the symbol layer. Pass { wipe: true } to replace the current set instead
  // of appending - useful when filters change. Pass { fitBounds: true } on
  // first load to zoom the map onto the resulting features.
  async loadActeursForBbox(
    bbox: ActeurBbox,
    options: {
      wipe?: boolean
      fitBounds?: boolean
      extraParams?: string
    } = {},
  ): Promise<void> {
    await this.#ensureActeursLayer()

    if (options.wipe) {
      this.#displayedUuids.clear()
      this.#setSourceData([])
    }

    this.#pendingFetchAbort?.abort()
    const abort = new AbortController()
    this.#pendingFetchAbort = abort

    const params = new URLSearchParams({
      bbox: [
        bbox.southWest.lng,
        bbox.southWest.lat,
        bbox.northEast.lng,
        bbox.northEast.lat,
      ].join(","),
      // Zoom drives spatial-thinning cell size server-side: at lower zooms
      // the backend uses bigger cells so markers stay visually spread out
      // instead of stacking onto a few pixels.
      zoom: this.map.getZoom().toFixed(2),
    })
    // We deliberately do NOT send exclude_uuids: a long session can balloon
    // the URL past the 8 KB request-line limit (HTTP 414). The frontend
    // already dedupes by uuid in #appendFeatures, so the backend is allowed
    // to return acteurs we already have - they're filtered out client-side.
    if (options.extraParams) {
      // The server hands us an already-encoded param string (e.g.
      // "groupe_actions=1,2&bonus=1"); merge into our URLSearchParams so we
      // get one cleanly-shaped query string.
      const extra = new URLSearchParams(options.extraParams)
      extra.forEach((value, key) => {
        params.set(key, value)
      })
    }

    let payload: GeoJsonResponse | undefined
    try {
      const response = await fetch(`${GEOJSON_ENDPOINT}?${params.toString()}`, {
        signal: abort.signal,
        headers: { Accept: "application/geo+json, application/json" },
      })
      if (!response.ok) {
        throw new Error(`acteurs.geojson returned ${response.status}`)
      }
      payload = (await response.json()) as GeoJsonResponse
    } catch (err) {
      if ((err as DOMException)?.name === "AbortError") return
      // Carte spec "Known fixes required": non-AbortError fetch failures must
      // be swallowed and logged. The user keeps whatever markers were already
      // on the map; subsequent pans can recover.
      console.error("acteurs.geojson fetch failed", err)
      return
    } finally {
      if (this.#pendingFetchAbort === abort) {
        this.#pendingFetchAbort = undefined
      }
    }
    if (!payload) return

    this.#appendFeatures(payload.features)

    if (options.fitBounds && this.#displayedUuids.size > 0) {
      const points: Array<[number, number]> = payload.features.map((f) => [
        f.geometry.coordinates[1], // lat
        f.geometry.coordinates[0], // lng
      ])
      this.fitBounds(points, undefined)
    }
  }

  // Fetch the K nearest acteurs around (lat, lng) from the KNN endpoint and
  // append them to the symbol layer. Camera fits to the bbox of the returned
  // features. Used by the address-search flow when the BAN result is a
  // street / housenumber / locality (not a municipality).
  async loadActeursNearest(
    lat: number,
    lng: number,
    options: { count?: number; extraParams?: string } = {},
  ): Promise<void> {
    await this.#ensureActeursLayer()

    this.#pendingFetchAbort?.abort()
    const abort = new AbortController()
    this.#pendingFetchAbort = abort

    const params = new URLSearchParams({
      lat: String(lat),
      lng: String(lng),
      count: String(options.count ?? 30),
    })
    if (options.extraParams) {
      const extra = new URLSearchParams(options.extraParams)
      extra.forEach((value, key) => {
        params.set(key, value)
      })
    }

    let payload: GeoJsonResponse | undefined
    try {
      const response = await fetch(
        `${GEOJSON_NEAR_ENDPOINT}?${params.toString()}`,
        {
          signal: abort.signal,
          headers: { Accept: "application/geo+json, application/json" },
        },
      )
      if (!response.ok) {
        throw new Error(`acteurs-near.geojson returned ${response.status}`)
      }
      payload = (await response.json()) as GeoJsonResponse
    } catch (err) {
      if ((err as DOMException)?.name === "AbortError") return
      console.error("acteurs-near.geojson fetch failed", err)
      return
    } finally {
      if (this.#pendingFetchAbort === abort) {
        this.#pendingFetchAbort = undefined
      }
    }
    if (!payload) return

    this.#appendFeatures(payload.features)

    // Always fit the camera to the result bbox: that's the whole point of
    // KNN — show the user the spread of nearest acteurs, even if they're
    // tens of kilometers away in a sparse area.
    if (payload.features.length > 0) {
      const points: Array<[number, number]> = payload.features.map((f) => [
        f.geometry.coordinates[1], // lat
        f.geometry.coordinates[0], // lng
      ])
      // Include the search center so the user's location stays in view too.
      points.push([lat, lng])
      this.fitBounds(points, undefined, { animate: true })
    }
  }

  async #ensureActeursLayer(): Promise<void> {
    if (!this.#iconsRegistered) {
      await registerActeurIcons(this.map)
      this.#iconsRegistered = true
    }

    if (this.#acteursSourceReady) return

    if (!this.map.getSource(ACTEURS_SOURCE_ID)) {
      this.map.addSource(ACTEURS_SOURCE_ID, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      })
    }

    if (!this.map.getLayer(ACTEURS_LAYER_ID)) {
      this.map.addLayer({
        id: ACTEURS_LAYER_ID,
        type: "symbol",
        source: ACTEURS_SOURCE_ID,
        layout: {
          "icon-image": ["get", "icon"],
          "icon-anchor": "bottom",
          "icon-allow-overlap": true,
          "icon-ignore-placement": true,
        },
      })

      this.map.on("click", ACTEURS_LAYER_ID, this.#onActeurClick.bind(this))
      this.map.on("mouseenter", ACTEURS_LAYER_ID, () => {
        this.map.getCanvas().style.cursor = "pointer"
      })
      this.map.on("mouseleave", ACTEURS_LAYER_ID, () => {
        this.map.getCanvas().style.cursor = ""
      })
    }

    this.#acteursSourceReady = true
  }

  #appendFeatures(features: ActeurFeature[]): void {
    // Per the carte spec, skip the source update entirely when a fetch
    // returns no fresh features. Avoids a 1-frame icon repaint on Safari/iOS
    // and protects against the symbol-collision "vanishing" perception.
    const fresh = features.filter((f) => !this.#displayedUuids.has(f.properties.uuid))
    if (fresh.length === 0) return

    this.#displayedFeatures = [...this.#displayedFeatures, ...fresh]
    for (const f of fresh) {
      this.#displayedUuids.add(f.properties.uuid)
    }
    this.#flushSource()

    // Telemetry: emit a soft alarm when the in-memory feature count exceeds
    // the threshold from the carte spec. The on-screen behavior is unchanged;
    // operators can use this signal to flip the LRU eviction feature flag if
    // sessions ever reach this size in practice.
    if (this.#displayedFeatures.length >= ACTEURS_SOFT_ALARM_THRESHOLD) {
      // Deduplicate: only fire once per session.
      if (!this.#softAlarmFired) {
        this.#softAlarmFired = true
        try {
          window.dispatchEvent(
            new CustomEvent("carte:displayedFeaturesAlarm", {
              detail: { count: this.#displayedFeatures.length },
            }),
          )
        } catch {
          // ignore
        }
      }
    }
  }

  #setSourceData(features: ActeurFeature[]): void {
    this.#displayedFeatures = features
    this.#flushSource()
  }

  #flushSource(): void {
    const source = this.map.getSource(ACTEURS_SOURCE_ID) as GeoJSONSource | undefined
    if (!source) return
    source.setData({
      type: "FeatureCollection",
      features: this.#displayedFeatures,
    })
  }

  #onActeurClick(event: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }): void {
    const feature = event.features?.[0]
    if (!feature) return
    const props = feature.properties as { detail_url?: string; uuid?: string }
    if (!props?.detail_url) return

    const frameId = (this.#controller as unknown as { acteurFrameIdValue?: string })
      .acteurFrameIdValue
    const frame = frameId ? document.getElementById(frameId) : null
    if (frame && "src" in frame) {
      ;(frame as HTMLIFrameElement).src = props.detail_url
    }

    this.#controller.dispatch("acteurSelected", {
      detail: { uuid: props.uuid, url: props.detail_url },
      bubbles: true,
    })
  }

  get displayedUuids(): ReadonlySet<string> {
    return this.#displayedUuids
  }

  // Called from MapController.disconnect(). Cancels any in-flight GeoJSON
  // fetch so it doesn't outlive the map and try to mutate a removed source.
  abortPendingFetch(): void {
    this.#pendingFetchAbort?.abort()
    this.#pendingFetchAbort = undefined
  }

  // Debug helper: returns the in-memory authoritative feature list, separately
  // from what MapLibre's source may have processed. Used to diagnose lost
  // markers during rapid pan/zoom sequences.
  get displayedFeatures(): ReadonlyArray<ActeurFeature> {
    return this.#displayedFeatures
  }

  // Draw (or update) a translucent red overlay around a search area, e.g. the
  // commune polygon when the user picks a city from the address autocomplete.
  // The polygon argument is a GeoJSON Feature or FeatureCollection.
  setSearchArea(polygon: GeoJSON.Feature | GeoJSON.FeatureCollection): void {
    const data: GeoJSON.FeatureCollection =
      polygon.type === "FeatureCollection"
        ? polygon
        : { type: "FeatureCollection", features: [polygon] }

    if (!this.map.getSource(SEARCH_AREA_SOURCE_ID)) {
      this.map.addSource(SEARCH_AREA_SOURCE_ID, { type: "geojson", data })
    } else {
      ;(this.map.getSource(SEARCH_AREA_SOURCE_ID) as GeoJSONSource).setData(data)
    }

    // Insert under the acteur symbol layer so pinpoints stay clickable on top
    // of the overlay.
    const beforeId = this.map.getLayer(ACTEURS_LAYER_ID) ? ACTEURS_LAYER_ID : undefined

    if (!this.map.getLayer(SEARCH_AREA_LINE_LAYER_ID)) {
      this.map.addLayer(
        {
          id: SEARCH_AREA_LINE_LAYER_ID,
          type: "line",
          source: SEARCH_AREA_SOURCE_ID,
          paint: {
            "line-color": SEARCH_AREA_COLOR,
            "line-width": 2,
          },
        },
        beforeId,
      )
    }
  }

  clearSearchArea(): void {
    if (this.map.getLayer(SEARCH_AREA_LINE_LAYER_ID)) {
      this.map.removeLayer(SEARCH_AREA_LINE_LAYER_ID)
    }
    if (this.map.getSource(SEARCH_AREA_SOURCE_ID)) {
      this.map.removeSource(SEARCH_AREA_SOURCE_ID)
    }
  }

  fitBounds(points, bboxValue, options: { animate?: boolean } = {}) {
    this.points = points ?? []
    this.bboxValue = bboxValue
    const fitBoundsOptions: FitBoundsOptions = {
      padding: this.mapPadding,
      // Default: instant. The ResizeObserver in initEventListener calls
      // fitBounds repeatedly while the layout is settling; animating those
      // calls would produce a janky cascade. Callers that want a smooth move
      // (e.g. the post-Turbo-swap initial fit on a new address) opt in via
      // { animate: true }.
      duration: options.animate ? 600 : 0,
      ...(options.animate && { essential: true }),
      ...(this.#useOsm && { maxZoom: DEFAULT_MAX_ZOOM - 1 }),
    }
    if (typeof bboxValue !== "undefined") {
      this.map.fitBounds(
        [
          [bboxValue.southWest.lng, bboxValue.southWest.lat],
          [bboxValue.northEast.lng, bboxValue.northEast.lat],
        ],
        fitBoundsOptions,
      )
    } else if (this.points.length > 0) {
      const lngs = this.points.map((point) => point[1])
      const lats = this.points.map((point) => point[0])
      const bounds: LngLatBoundsLike = [
        [Math.min(...lngs), Math.min(...lats)], // South-west
        [Math.max(...lngs), Math.max(...lats)], // North-east
      ]
      this.map.fitBounds(bounds, fitBoundsOptions)
    }
  }

  #addZoomControl() {
    this.map.addControl(
      new maplibregl.NavigationControl({
        visualizePitch: false,
        visualizeRoll: false,
        showZoom: true,
        showCompass: false,
      }),
      "top-left",
    )
  }

  #dispatchMapChangedEvent(): void {
    const bounds = this.map.getBounds()
    const detail = {
      center: bounds.getCenter(),
      southWest: bounds.getSouthWest(),
      northEast: bounds.getNorthEast(),
    }
    const event = new CustomEvent("maplibre:mapChanged", {
      detail,
      bubbles: true,
    })
    this.#controller.mapChanged(event)
  }

  initEventListener(): void {
    // Map width is set here so that it can be compared during each resize.
    // If the map container grew, the value should be different, hence
    // considering the map to not be idle.
    // Once the mapWidth has stopped growing, we can consider the map as idle
    // and add events that will help set its boundaries and zoom level.
    this.#mapWidthBeforeResize = this.map.getContainer().offsetWidth
    const resizeObserver = new ResizeObserver(() => {
      this.map.resize()
      // Re-fit to the initial bounds only while the layout is still settling.
      // After we install the `moveend` listener (resizeStopped), the user is
      // in control and any further fitBounds calls would yank the camera back
      // to the initial view — defeating zoom/pan and the auto-search-on-pan
      // behavior.
      if (!this.#layoutSettled) {
        this.fitBounds(this.points, this.bboxValue)
      }
      const currentMapWidth = this.map.getContainer().offsetWidth
      const resizeStopped =
        this.#mapWidthBeforeResize > 0 && this.#mapWidthBeforeResize === currentMapWidth
      if (resizeStopped) {
        // The 1s timeout here is arbitrary and prevents adding listener
        // when the map is still moving.
        setTimeout(() => {
          this.#layoutSettled = true
          this.map.on("moveend", this.#dispatchMapChangedEvent.bind(this))
          resizeObserver.disconnect()
        }, 1000)
      }
      this.#mapWidthBeforeResize = currentMapWidth
    })
    resizeObserver.observe(this.map.getContainer())
  }
}
