/**
This file holds constants and functions that are used both
by Stimulus controllers and Leaflet instance.

It was created / use mainly to prevent errors when running
tests.
*/

export const ACTIVE_PINPOINT_CLASSNAME = "active-pinpoint"
export const URL_PARAM_NAME_FOR_IFRAME_SCRIPT_MODE = "s"

export function clearActivePinpoints() {
  document.querySelectorAll(`.${ACTIVE_PINPOINT_CLASSNAME}`).forEach((element) => {
    element.classList.remove(ACTIVE_PINPOINT_CLASSNAME)
  })
}

export function removeHash() {
  history.pushState(
    "",
    document.title,
    window.location.pathname + window.location.search,
  )
}

/**
 * Compute the available vertical space below `frameTop` inside the document
 * body, leaving `margin` pixels between the bottom edge and the body bottom.
 *
 * Returns 0 if there is no room left rather than a negative value, so callers
 * can pass the result straight to a CSS length.
 */
export function computeAvailableHeight(
  frameTop: number,
  bodyHeight: number,
  margin: number,
): number {
  return Math.max(0, bodyHeight - frameTop - margin)
}
