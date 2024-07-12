window.addEventListener("message", (event) => {
  const domain = new URL(event.origin).hostname
  if (event.data === "ademe" && (domain === 'localhost' || domain.endsWith("ademe.fr"))) {
    document.querySelector("#logo")?.remove()
  }
});
