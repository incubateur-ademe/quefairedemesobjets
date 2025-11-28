/**
Deprecation notice : this will be deprecated as soon as the map
will be embedded without an iframe but using a turbo-frame in a
near future (around january 2025)
*/

const IFRAME_REFERRER_SESSION_KEY = "qf_ifr"

export function areWeInAnIframe() {
  let weAreInAnIframe = false
  let referrer

  // First, try to get the stored referrer from sessionStorage
  // This ensures we don't lose it on subsequent navigations
  const storedReferrer = sessionStorage.getItem(IFRAME_REFERRER_SESSION_KEY)
  if (storedReferrer) {
    referrer = storedReferrer
  }

  try {
    if (window.self !== window.top) {
      weAreInAnIframe = true
      // For same-origin iframes, we can access the parent URL directly
      referrer = window.top?.location.href
    }
  } catch (e) {
    // Unable to access window.top
    // this might be due to cross-origin restrictions.
    // Assuming it's inside an iframe.
    weAreInAnIframe = true
  }

  // For cross-origin iframes, document.referrer contains the parent URL
  // But only on the first load - so we need to persist it
  if (document.referrer && !document.referrer.includes(document.location.origin)) {
    weAreInAnIframe = true

    // Only set referrer if we don't already have one
    // This prevents overwriting the original referrer on subsequent navigations
    if (!referrer) {
      referrer = document.referrer
    }
  }

  // Persist the referrer in sessionStorage so it survives navigations
  // Only store if we have a referrer and are in an iframe
  if (weAreInAnIframe && referrer && !storedReferrer) {
    try {
      sessionStorage.setItem(IFRAME_REFERRER_SESSION_KEY, referrer)
    } catch (e) {
      // SessionStorage might not be available (privacy mode, etc.)
      console.warn("Unable to persist iframe referrer:", e)
    }
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
