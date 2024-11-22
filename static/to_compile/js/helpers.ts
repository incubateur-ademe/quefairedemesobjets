/**
This file holds constants and functions that are used both
by Stimulus controllers and Leaflet instance.

It was created / use mainly to prevent errors when running
tests.
*/

export const ACTIVE_PINPOINT_CLASSNAME = "active-pinpoint"

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
