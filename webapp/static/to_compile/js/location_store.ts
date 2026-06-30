/**
 * Single source of truth for the user's map location (adresse + lat/lon).
 *
 * This is a plain module, NOT a Stimulus controller, on purpose: the location is
 * read by four unrelated controllers (`ab-test`, `frame-location`,
 * `search-solution-form`, `location`) at four different moments, and some of
 * them (the lazy-frame `src` injection) need it *synchronously* before a fetch.
 * A controller would force them to reach a sibling controller instance — either
 * via Stimulus outlets (whose connect callbacks re-fire on every Turbo
 * re-render, which is the very bug we are removing) or via async event
 * request/response. A module sidesteps both: everyone imports the same
 * functions and reads `sessionStorage` directly.
 *
 * sessionStorage is the cross-page carrier (cookies are off-limits for GDPR
 * reasons in this app). The keys are also read by the analytics controller.
 */

export const LOCATION_KEYS = {
  adresse: "adresse",
  latitude: "latitude",
  longitude: "longitude",
} as const

export interface StoredLocation {
  adresse: string | null
  latitude: string | null
  longitude: string | null
}

/** Read the location currently persisted in sessionStorage. */
export function readStoredLocation(): StoredLocation {
  return {
    adresse: sessionStorage.getItem(LOCATION_KEYS.adresse),
    latitude: sessionStorage.getItem(LOCATION_KEYS.latitude),
    longitude: sessionStorage.getItem(LOCATION_KEYS.longitude),
  }
}

/**
 * A location is usable for a backend search only when both coordinates exist.
 * Mirrors the server-side guard (`if latitude and longitude`) so an incomplete
 * location is treated the same client- and server-side.
 */
export function hasCompleteLocation(location: StoredLocation): boolean {
  return Boolean(location.latitude && location.longitude)
}

/** Persist a location, writing each key only when it is present and changed. */
export function persistLocation(location: Partial<StoredLocation>): void {
  persistKey(LOCATION_KEYS.adresse, location.adresse)
  persistKey(LOCATION_KEYS.latitude, location.latitude)
  persistKey(LOCATION_KEYS.longitude, location.longitude)
}

function persistKey(key: string, value: string | null | undefined): void {
  if (!value) return
  if (value !== sessionStorage.getItem(key)) {
    sessionStorage.setItem(key, value)
  }
}

/**
 * Return `src` with `location` appended as namespaced MapForm params
 * (`{prefix}-latitude`, `-longitude`, `-adresse`, where `prefix` is
 * `{map_container_id}_map`).
 *
 * The server only accepts the namespaced names (bare `latitude`/`longitude`
 * are ignored). Existing query params (e.g. `sc_id`) are preserved. When the
 * location has no coordinates the `src` is returned untouched, so the frame
 * loads exactly as it would without an experiment / for a first-time visitor.
 */
export function injectLocationIntoSrc(
  src: string,
  prefix: string,
  location: StoredLocation,
): string {
  if (!src || !prefix) return src
  if (!hasCompleteLocation(location)) return src

  const url = new URL(src, window.location.origin)
  url.searchParams.set(`${prefix}-latitude`, location.latitude!)
  url.searchParams.set(`${prefix}-longitude`, location.longitude!)
  if (location.adresse) {
    url.searchParams.set(`${prefix}-adresse`, location.adresse)
  }

  // Keep the value relative, like the original server-rendered `src`.
  return `${url.pathname}${url.search}`
}
