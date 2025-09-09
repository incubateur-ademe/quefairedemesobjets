import maplibregl, { LngLat, LngLatBoundsLike, Map, Marker } from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import MapController from "../controllers/carte/map_controller"
import { ACTIVE_PINPOINT_CLASSNAME, clearActivePinpoints } from "./helpers"
import type { Location } from "./types"
const DEFAULT_LOCATION: LngLat = new LngLat(2.213749, 46.227638)
const DEFAULT_ZOOM: number = 5
const DEFAULT_MAX_ZOOM: number = 18

export class SolutionMap {
  map: Map
  #location: Location
  #mapWidthBeforeResize: number
  #controller: MapController
  bboxValue?: Array<Number>
  points: Array<Array<Number>>
  mapPadding: number = 50

  constructor({
    selector,
    location,
    controller,
  }: {
    selector: HTMLDivElement
    location: Location
    controller: MapController
  }) {
    this.#location = location
    this.#controller = controller

    this.map = new Map({
      container: selector,
      style: {
        version: 8,
        sources: {
          "carto-light": {
            type: "raster",
            tiles: [
              "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
              "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
              "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors, © CARTO",
          },
        },
        layers: [
          {
            id: "carto-light-layer",
            type: "raster",
            source: "carto-light",
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: DEFAULT_LOCATION,
      zoom: DEFAULT_ZOOM,
      maxZoom: DEFAULT_MAX_ZOOM,
      // Ajouter les contrôles de zoom
    })
    this.#manageZoomControl()

    if (
      this.#location.latitude !== undefined &&
      this.#location.longitude !== undefined
    ) {
      new maplibregl.Marker({
        element: this.#generateHomeHTMLMarker(),
      })
        .setLngLat([this.#location.longitude, this.#location.latitude])
        .setPopup(
          new maplibregl.Popup().setHTML("<p><strong>Vous êtes ici !</strong></p>"),
        )
        .addTo(this.map)
    }
  }

  #generateHomeHTMLMarker() {
    const homePinPoint = document.getElementById("pinpoint-home")
    if (!homePinPoint) {
      return null
    }
    homePinPoint.classList.remove("qf-invisible")
    return homePinPoint
  }

  addActorMarkersToMap(actors: Array<HTMLElement>, bboxValue?: Array<Number>): void {
    const points: Array<Array<Number>> = []
    const addedActors: Array<string> = []
    actors.forEach(function (actor: HTMLElement) {
      if (addedActors.includes(actor.dataset?.uuid || "")) {
        // Ensure actors are not added twice on the map.
        // This can happen and can causes visual glitches.
        // ID of markers being duplicated, these are wrongly rendered
        // without borders.
        return
      }

      const longitude = actor.dataset?.longitude
      const latitude = actor.dataset?.latitude

      if (longitude && latitude) {
        let longitudeFloat = parseFloat(longitude.replace(",", "."))
        let latitudeFloat = parseFloat(latitude.replace(",", "."))
        actor.addEventListener("click", () => {
          this.#onClickMarker(actor)
        })
        actor.classList.remove("qf-invisible")

        const marker: Marker = new maplibregl.Marker({
          element: actor,
        }).setLngLat([longitudeFloat, latitudeFloat])

        marker.addTo(this.map)
        addedActors.push(actor.dataset?.uuid || "")
        points.push([latitudeFloat, longitudeFloat])
      }
    }, this)
    this.fitBounds(points, bboxValue)
  }

  fitBounds(points, bboxValue) {
    this.points = points
    this.bboxValue = bboxValue
    if (typeof bboxValue !== "undefined") {
      this.map.fitBounds(
        [
          [bboxValue.southWest.lng, bboxValue.southWest.lat],
          [bboxValue.northEast.lng, bboxValue.northEast.lat],
        ],
        {
          padding: this.mapPadding,
          duration: 0,
        },
      )
    } else if (points.length > 0) {
      // Compute bbox from points
      const lngs = points.map((point) => point[1])
      const lats = points.map((point) => point[0])
      const bounds: LngLatBoundsLike = [
        [Math.min(...lngs), Math.min(...lats)], // Sud-ouest
        [Math.max(...lngs), Math.max(...lats)], // Nord-est
      ]
      this.map.fitBounds(bounds, {
        padding: this.mapPadding,
        duration: 0,
      })
    }
  }

  #onClickMarker(actorMarker: HTMLDivElement) {
    clearActivePinpoints()
    actorMarker.classList.add(ACTIVE_PINPOINT_CLASSNAME)
    this.#controller.setActiveActeur(actorMarker.dataset.uuid || "")
  }

  #manageZoomControl() {
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
