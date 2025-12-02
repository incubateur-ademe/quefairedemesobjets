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
