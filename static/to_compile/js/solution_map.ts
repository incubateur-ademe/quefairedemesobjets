import maplibregl, {
  FitBoundsOptions,
  LngLat,
  LngLatBoundsLike,
  Map,
  Marker,
} from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import "carte-facile/dist/carte-facile.css"
import { mapStyles, Overlay, addOverlay } from "carte-facile"
import MapController from "../controllers/carte/map_controller"
import type { Location } from "./types"
const DEFAULT_LOCATION: LngLat = new LngLat(2.213749, 46.227638)
const DEFAULT_INITIAL_ZOOM: number = 5
const DEFAULT_MAX_ZOOM: number = 18.9 // Carte Facile recommendation

export class SolutionMap {
  map: Map
  #location: Location
  #mapWidthBeforeResize: number
  #controller: MapController
  bboxValue?: Array<Number>
  points: Array<Array<Number>>
  mapPadding: number = 50
  initialZoom: number = DEFAULT_INITIAL_ZOOM

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
    const useOsm = theme === "osm"

    if (useOsm) {
      // OSM tiles for Django admin
      this.map = new Map({
        container: selector,
        style: {
          version: 8,
          sources: {
            osm: {
              type: "raster",
              tiles: [
                "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
              ],
              tileSize: 256,
            },
          },
          layers: [{ type: "raster", id: "osm-layer", source: "osm" }],
        },
        zoom: initialZoom,
        maxZoom: 20,
        center: DEFAULT_LOCATION,
        attributionControl: {
          compact: true,
          customAttribution: "© OpenStreetMap contributors",
        },
      })
    } else {
      // Carte Facile for public site
      this.map = new Map({
        container: selector,
        style: mapStyles.desaturated,
        zoom: initialZoom,
        maxZoom: DEFAULT_MAX_ZOOM,
        center: DEFAULT_LOCATION,
        attributionControl: {
          compact: true,
        },
      })
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
        },
        bubbles: true,
        cancelable: false,
      })
    })
  }

  fitBounds(points, bboxValue) {
    this.points = points
    this.bboxValue = bboxValue
    const fitBoundsOptions: FitBoundsOptions = {
      padding: this.mapPadding,
      duration: 0,
    }
    if (typeof bboxValue !== "undefined") {
      this.map.fitBounds(
        [
          [bboxValue.southWest.lng, bboxValue.southWest.lat],
          [bboxValue.northEast.lng, bboxValue.northEast.lat],
        ],
        fitBoundsOptions,
      )
    } else if (points.length > 0) {
      // Compute bbox from points
      const lngs = points.map((point) => point[1])
      const lats = points.map((point) => point[0])
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
      this.fitBounds(this.points, this.bboxValue)
      const currentMapWidth = this.map.getContainer().offsetWidth
      const resizeStopped =
        this.#mapWidthBeforeResize > 0 && this.#mapWidthBeforeResize === currentMapWidth
      if (resizeStopped) {
        // The 1s timeout here is arbitrary and prevents adding listener
        // when the map is still moving.
        setTimeout(() => {
          this.map.on("moveend", this.#dispatchMapChangedEvent.bind(this))
          resizeObserver.disconnect()
        }, 1000)
      }
      this.#mapWidthBeforeResize = currentMapWidth
    })
    resizeObserver.observe(this.map.getContainer())
  }
}
