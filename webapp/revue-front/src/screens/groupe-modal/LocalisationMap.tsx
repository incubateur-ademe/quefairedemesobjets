import "maplibre-gl/dist/maplibre-gl.css"

import maplibreWorkerSource from "bundle-text:maplibre-gl/dist/maplibre-gl-worker.mjs"
import { LngLatBounds, Map, Marker, NavigationControl, setWorkerUrl } from "maplibre-gl"
import { useEffect, useRef } from "react"

import type { Point } from "../../api/types"

let workerReady = false

/** maplibre-gl v6 resolves its worker from import.meta.url, which Parcel does not
 * preserve: the bundled worker source is inlined as a blob URL (as in the webapp),
 * created with the first map. */
function setupWorker() {
  if (!workerReady) {
    setWorkerUrl(
      URL.createObjectURL(
        new Blob([maplibreWorkerSource], { type: "text/javascript" }),
      ),
    )
    workerReady = true
  }
}

/** Marker of the map: a point of the groupe, or the localisation of the
 * établissement in the Annuaire des entreprises. */
export type MarkerKey = Point["key"] | "AnnuaireEntreprises"
export type MapPoint = Omit<Point, "key"> & { key: MarkerKey }

/** Markers of the localisation tab, as in the admin (suggestion-map-update). */
export const MARKERS: Record<
  MarkerKey,
  { color: string; text: string; label: string }
> = {
  Origin: {
    color: "var(--mk-grey)",
    text: "",
    label: "Acteur initial avant l’application de la correction (acteur en base)",
  },
  Acteur: {
    color: "var(--mk-green)",
    text: "A",
    label: "Acteur importé après application de la modification",
  },
  RevisionActeur: {
    color: "var(--mk-blue)",
    text: "▶",
    label: "Correction après application de la modification",
  },
  ParentRevisionActeur: {
    color: "var(--mk-red)",
    text: "⏩",
    label: "Parent après application de la modification",
  },
  AnnuaireEntreprises: {
    color: "var(--mk-purple)",
    text: "AE",
    label: "Établissement dans l’Annuaire des entreprises",
  },
}

const OSM_STYLE = {
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
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ type: "raster" as const, id: "osm", source: "osm" }],
}

function markerElement(key: MarkerKey, draggable: boolean) {
  const element = document.createElement("div")
  element.className = `pin${draggable ? " pin--drag" : ""}`
  element.dataset.markerKey = key
  element.title = MARKERS[key].label
  element.style.setProperty("--pin-color", MARKERS[key].color)
  element.innerHTML = `<span class="pin__head"><span class="pin__text"></span></span>`
  element.querySelector(".pin__text")!.textContent = MARKERS[key].text
  return element
}

/** Map with a marker per point. Releasing a draggable marker calls `onMove`;
 * clicking a marker calls `onFocus`; the `focused` marker is shown above the
 * others. */
export function LocalisationMap({
  points,
  focused = null,
  onMove,
  onFocus,
}: {
  points: MapPoint[]
  focused?: MarkerKey | null
  onMove: (key: MarkerKey, latitude: number, longitude: number) => void
  onFocus?: (key: MarkerKey) => void
}) {
  const container = useRef<HTMLDivElement>(null)
  const markers = useRef<Partial<Record<MarkerKey, HTMLElement>>>({})
  const callbacks = useRef({ onMove, onFocus })
  useEffect(() => {
    callbacks.current = { onMove, onFocus }
  })

  const signature = JSON.stringify(points)
  useEffect(() => {
    if (!container.current) {
      return
    }
    setupWorker()
    const map = new Map({
      container: container.current,
      style: OSM_STYLE,
      center: points.length ? [points[0].longitude, points[0].latitude] : [2.2, 46.2],
      zoom: points.length ? 15 : 5,
      maxZoom: 18,
      attributionControl: { compact: true },
    })
    map.addControl(new NavigationControl({ showCompass: false }))
    markers.current = {}
    for (const point of points) {
      const element = markerElement(point.key, point.draggable)
      element.addEventListener("click", () => callbacks.current.onFocus?.(point.key))
      markers.current[point.key] = element
      const marker = new Marker({
        element,
        anchor: "bottom",
        draggable: point.draggable,
      })
        .setLngLat([point.longitude, point.latitude])
        .addTo(map)
      if (point.draggable) {
        // Saved as soon as the marker is released, without confirmation
        marker.on("dragend", () => {
          const { lat, lng } = marker.getLngLat()
          callbacks.current.onMove(point.key, lat, lng)
        })
      }
    }
    if (points.length > 1) {
      const bounds = new LngLatBounds()
      points.forEach((point) => bounds.extend([point.longitude, point.latitude]))
      map.fitBounds(bounds, { padding: 60, maxZoom: 17, duration: 0 })
    }
    return () => map.remove()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature])

  // The focused marker goes above the others (markers overlap when the
  // positions are close)
  useEffect(() => {
    for (const [key, element] of Object.entries(markers.current)) {
      const isFocused = key === focused
      element.style.zIndex = isFocused ? "10" : ""
      element.classList.toggle("pin--focused", isFocused)
    }
  }, [focused, signature])

  return <div ref={container} className="mapbox" aria-label="Carte de localisation" />
}
