import iframeResize from "@iframe-resizer/parent"
import { URL_PARAM_NAME_FOR_IFRAME_SCRIPT_MODE } from "../js/helpers"

const script = document.currentScript as HTMLScriptElement
const slug = script?.dataset?.objet
const epci = script?.dataset?.epci
let origin = new URL(script?.getAttribute("src")).origin

if (process.env.BASE_URL) {
  origin = process.env.BASE_URL
}

function initScript() {
  const parts = [origin]
  const iframeResizerOptions = { license: "GPLv3" }

  if (slug) {
    parts.push("dechet", slug)
  }

  const searchParams = new URLSearchParams()
  if (epci) {
    searchParams.set("epci", epci)
  }

  searchParams.set("iframe", "")
  searchParams.set(URL_PARAM_NAME_FOR_IFRAME_SCRIPT_MODE, "1")
  const src = `${parts.join("/")}?${searchParams.toString()}`
  const iframe = document.createElement("iframe")
  const iframeAttributes = {
    id: "quefairedemesdechets-assistant",
    src,
    style: "border: none; width: 100%; display: block; margin: 0 auto;",
    allowfullscreen: true,
    allow: "geolocation; clipboard-write",
    title: "Que faire de mes objets et déchets",
  }

  if (script?.dataset?.testid) {
    iframeAttributes["data-testid"] = script.dataset.testid
  }

  const debugReferrer = typeof script?.dataset?.debugReferrer !== "undefined"
  if (debugReferrer) {
    iframeAttributes.referrerPolicy = "no-referrer"
  }

  for (var key in iframeAttributes) {
    iframe.setAttribute(key, iframeAttributes[key])
  }

  script.parentNode?.insertBefore(iframe, script)
  iframe.onload = () => {
    iframeResize(iframeResizerOptions, iframe)
  }
}
if (document.readyState === "loading") {
  // Loading hasn't finished yet
  document.addEventListener("DOMContentLoaded", initScript)
} else {
  // `DOMContentLoaded` has already fired
  initScript()
}
