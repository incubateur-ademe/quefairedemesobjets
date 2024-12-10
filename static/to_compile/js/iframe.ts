/**
Deprecation notice : this will be deprecated as soon as the map
will be embedded without an iframe but using a turbo-frame in a
near future (around january 2025)
*/
window.addEventListener("message", (event) => {
  const domain = new URL(event.origin).hostname
  if (event.data === "ademe" && (domain === 'localhost' || domain.endsWith(".ademe.fr") || domain === "quefairedemesobjets-preprod.osc-fr1.scalingo.io")) {
    document.querySelector("#logo")?.remove()
  }
});
