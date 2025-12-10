import { Controller } from "@hotwired/stimulus"
import { LngLatBoundsLike, Map, Marker } from "maplibre-gl"

import "maplibre-gl/dist/maplibre-gl.css"
import { SolutionMap } from "../../js/solution_map"

const DEFAULT_INITIAL_ZOOM: number = 14
const DEFAULT_MAX_ZOOM: number = 20

interface LocalisationPoint {
  latitude: number
  longitude: number
  color: string
  draggable: boolean
}

interface LocalisationData {
  points: LocalisationPoint[]
}

export default class extends Controller<HTMLElement> {
  map: Map
  static targets = ["mapContainer", "latslongs"]

  declare readonly mapContainerTarget: HTMLDivElement
  declare readonly latslongsTarget: HTMLScriptElement

  solutionMap: SolutionMap | null = null
  currentMarker: Marker | null = null
  proposedMarker: Marker | null = null
  draggableMarker: Marker | null = null
  localisationData: LocalisationData | null = null

  connect() {
    this.localisationData = JSON.parse(
      this.latslongsTarget.dataset.localisationValue || "{}",
    )
    this.map = new Map({
      container: this.mapContainerTarget,
      style: {
        version: 8,
        sources: {
          "raster-tiles": {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            minzoom: 0,
            maxzoom: DEFAULT_MAX_ZOOM - 1,
          },
        },
        layers: [
          {
            id: "simple-tiles",
            type: "raster",
            source: "raster-tiles",
          },
        ],
      },
      zoom: DEFAULT_INITIAL_ZOOM,
      maxZoom: DEFAULT_MAX_ZOOM,
      attributionControl: {
        compact: true,
        customAttribution: "© OpenStreetMap contributors",
      },
    })
    // Ajouter les contrôles de zoom
    // this.#addZoomControl()
    const boundsPoints: Array<Array<Number>> = []
    if (this.localisationData && this.localisationData.points) {
      this.localisationData.points.forEach((point) => {
        const marker = new Marker({
          color: point.color,
          draggable: point.draggable,
        })
          .setLngLat([point.longitude, point.latitude])
          .addTo(this.map)

        if (point.draggable) {
          this.draggableMarker = marker
          this.#setupMarkerDragListener(marker)
        }

        boundsPoints.push([point.longitude, point.latitude])
      })

      // Fit bounds on points
      if (boundsPoints.length > 0) {
        const lngs = boundsPoints.map((point) => point[0] as number)
        const lats = boundsPoints.map((point) => point[1] as number)
        const bounds: LngLatBoundsLike = [
          [Math.min(...lngs), Math.min(...lats)], // Sud-ouest
          [Math.max(...lngs), Math.max(...lats)], // Nord-est
        ]
        this.map.fitBounds(bounds, {
          padding: 50,
          duration: 0,
        })
      }
    }
  }

  #setupMarkerDragListener(marker: Marker) {
    marker.on("dragend", () => {
      const lngLat = marker.getLngLat()
      this.dispatch("markerDragged", {
        detail: {
          latitude: lngLat.lat.toString(),
          longitude: lngLat.lng.toString(),
        },
        bubbles: true,
        cancelable: false,
      })
    })
  }
}
