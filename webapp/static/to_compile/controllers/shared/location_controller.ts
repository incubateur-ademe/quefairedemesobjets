import { Controller } from "@hotwired/stimulus"
import { persistLocation } from "../../js/location_store"

export const LOCATION_CHANGED_EVENT = "qf:location-changed"

export interface LocationDetail {
  adresse: string
  latitude: string
  longitude: string
}

/**
 * Page-level coordinator (mounted on <body>) for the user's map location.
 *
 * It is the DOM-bound half of the location system: it listens for address picks
 * and broadcasts them. The storage half lives in `location_store.ts` so the
 * other controllers (ab-test, frame-location, search-solution-form) can read the
 * location synchronously without reaching into this controller — no Stimulus
 * outlets, which is what caused phantom submits on Turbo re-renders.
 *
 * Flow on an address pick:
 *   autocomplete `…:change` (body data-action)
 *     -> persistAndBroadcast: persist to sessionStorage + emit
 *        `qf:location-changed` on document
 *     -> each carte form listens and submits itself.
 */
export default class LocationController extends Controller<HTMLElement> {
  // Persist a freshly picked location and notify every carte on the page.
  persistAndBroadcast(event: CustomEvent<LocationDetail>) {
    const detail = event.detail
    if (!detail) return

    persistLocation(detail)
    document.dispatchEvent(new CustomEvent(LOCATION_CHANGED_EVENT, { detail }))
  }
}
