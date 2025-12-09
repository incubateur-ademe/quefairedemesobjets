import { Controller } from "@hotwired/stimulus"
import { LngLatBoundsLike, Map, Marker } from "maplibre-gl"

import "maplibre-gl/dist/maplibre-gl.css"
import { SolutionMap } from "../../js/solution_map"

const DEFAULT_INITIAL_ZOOM: number = 14
const DEFAULT_MAX_ZOOM: number = 21

interface LocalisationData {
  latitude: {
    displayed_value: string
    updated_displayed_value: string
    new_value: string
    old_value: string
  }
  longitude: {
    displayed_value: string
    updated_displayed_value: string
    new_value: string
    old_value: string
  }
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
          "carto-light": {
            type: "raster",
            tiles: [
              "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
              "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
              "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
          },
        },
        layers: [
          {
            id: "carto-light-layer",
            type: "raster",
            source: "carto-light",
            minzoom: 0,
            maxzoom: DEFAULT_MAX_ZOOM,
          },
        ],
      },
      zoom: DEFAULT_INITIAL_ZOOM,
      maxZoom: DEFAULT_MAX_ZOOM - 1,
      attributionControl: {
        compact: true,
        customAttribution: "© OpenStreetMap contributors, © CARTO",
      },
    })
    // Ajouter les contrôles de zoom
    // this.#addZoomControl()
    const points: Array<Array<Number>> = []
    if (this.localisationData) {
      if (
        this.localisationData.latitude.old_value &&
        this.localisationData.longitude.old_value
      ) {
        new Marker({ color: "red" })
          .setLngLat([
            parseFloat(this.localisationData.longitude.old_value),
            parseFloat(this.localisationData.latitude.old_value),
          ])
          .addTo(this.map)
        points.push([
          parseFloat(this.localisationData.longitude.old_value),
          parseFloat(this.localisationData.latitude.old_value),
        ])
      }
      if (
        this.localisationData.latitude.new_value &&
        this.localisationData.longitude.new_value
      ) {
        new Marker({ color: "#26A69A" })
          .setLngLat([
            parseFloat(this.localisationData.longitude.new_value),
            parseFloat(this.localisationData.latitude.new_value),
          ])
          .addTo(this.map)
        points.push([
          parseFloat(this.localisationData.longitude.new_value),
          parseFloat(this.localisationData.latitude.new_value),
        ])
      }
      if (
        this.localisationData.latitude.updated_displayed_value &&
        this.localisationData.longitude.updated_displayed_value
      ) {
        this.draggableMarker = new Marker({ color: "#00695C", draggable: true })
          .setLngLat([
            parseFloat(this.localisationData.longitude.updated_displayed_value),
            parseFloat(this.localisationData.latitude.updated_displayed_value),
          ])
          .addTo(this.map)
        this.#setupMarkerDragListener(this.draggableMarker)
        points.push([
          parseFloat(this.localisationData.longitude.updated_displayed_value),
          parseFloat(this.localisationData.latitude.updated_displayed_value),
        ])
      } else {
        if (
          this.localisationData.latitude.displayed_value &&
          this.localisationData.longitude.displayed_value
        ) {
          this.draggableMarker = new Marker({ color: "#00695C", draggable: true })
            .setLngLat([
              parseFloat(this.localisationData.longitude.displayed_value),
              parseFloat(this.localisationData.latitude.displayed_value),
            ])
            .addTo(this.map)
          this.#setupMarkerDragListener(this.draggableMarker)
          points.push([
            parseFloat(this.localisationData.longitude.displayed_value),
            parseFloat(this.localisationData.latitude.displayed_value),
          ])
        }
      }
      // Fit bounds on points
      if (points.length > 0) {
        const lngs = points.map((point) => point[0] as number)
        const lats = points.map((point) => point[1] as number)
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
