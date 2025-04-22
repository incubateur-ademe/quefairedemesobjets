/**
Deprecation notice : this will be deprecated as soon as the map
will be embedded without an iframe but using a turbo-frame in a
near future (around january 2025)
*/
function removeUnwantedElements() {
  const domain = new URL(document.referrer).hostname
  if (domain === 'localhost' || domain.endsWith(".ademe.fr") || domain.endsWith(".ademe.dev")) {
    for (const elementToRemove of document.querySelectorAll("[data-remove-if-internal]")) {
      elementToRemove.remove()
    }
  }
}
window.addEventListener("DOMContentLoaded", removeUnwantedElements);
document.addEventListener("turbo:frame-load", removeUnwantedElements)
