/**
Deprecation notice : this will be deprecated as soon as the map
will be embedded without an iframe but using a turbo-frame in a
near future (around january 2025)
*/
window.addEventListener("DOMContentLoaded", (event) => {
  const domain = new URL(document.referrer).hostname
  if (true || domain === 'localhost' || domain.endsWith(".ademe.fr") || domain === "quefairedemesobjets-preprod.osc-fr1.scalingo.io") {
    for (const elementToRemove of document.querySelectorAll("[data-remove-if-internal]")) {
      console.log({ elementToRemove })
      elementToRemove.remove()
    }
  }
});
