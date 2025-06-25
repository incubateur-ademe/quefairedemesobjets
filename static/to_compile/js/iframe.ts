/**
Deprecation notice : this will be deprecated as soon as the map
will be embedded without an iframe but using a turbo-frame in a
near future (around january 2025)
*/

export function areWeInAnIframe() {
  let weAreInAnIframe = false
  let referrer

  try {
    if (window.self !== window.top) {
      weAreInAnIframe = true
      referrer = window.top?.location.href
    }
  } catch (e) {
    // Unable to access window.top
    // this might be due to cross-origin restrictions.
    // Assuming it's inside an iframe.
    weAreInAnIframe = true
  }

  if (document.referrer && !document.referrer.includes(document.location.origin)) {
    weAreInAnIframe = true
  }

  return [weAreInAnIframe, referrer]
}
function removeUnwantedElements() {
  if (!document.referrer) {
    return
  }
  const domain = new URL(document.referrer).hostname
  const domainIsInternal =
    domain === "localhost" ||
    domain.endsWith(".ademe.fr") ||
    domain.endsWith(".ademe.dev")
  if (domainIsInternal) {
    for (const elementToRemove of document.querySelectorAll(
      "[data-remove-if-internal]",
    )) {
      elementToRemove.remove()
    }
  }
}
window.addEventListener("DOMContentLoaded", removeUnwantedElements)
document.addEventListener("turbo:frame-load", removeUnwantedElements)
