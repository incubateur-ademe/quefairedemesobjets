import type { Map as MapLibreMap, Marker } from "maplibre-gl"

import type { Place } from "./visible_places"

export const CANVAS_ID = "assistant-carte-canvas"

/** Hangs on the canvas, a Turbo permanent element: the map outlives screens. */
export type PersistedMap = {
  map: MapLibreMap
  Marker: typeof Marker
  markers: Map<string, Marker>
  places: Place[]
  addressMarker: Marker | null
  /** Gestes + objet: when they change, the pins are wrong and start over. */
  key: string
  address: [number, number]
  lastRequestedUrl: string
  /** The first places found around a new address frame the view, once. */
  needsFit: boolean
  onMoveEnd: (() => void) | null
}

export type CanvasWithMap = HTMLElement & { assistantMap?: PersistedMap }
