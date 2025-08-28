import iframeResize from "@iframe-resizer/parent"
import { URL_PARAM_NAME_FOR_IFRAME_SCRIPT_MODE } from "../js/helpers"
import { iframeResizer } from "@iframe-resizer/child"

const script = document.currentScript as HTMLScriptElement
const slug = script?.dataset?.objet
const epci = script?.dataset?.epci
let origin = new URL(script?.getAttribute("src")).origin

if (process.env.BASE_URL) {
  origin = process.env.BASE_URL
}

function generateBackLink(iframe: HTMLIFrameElement) {
  const backlinkTag = document.createElement("div")
  backlinkTag.setAttribute(
    "style",
    "font-size: 0.9rem; text-align: center; padding-top: 0.5rem;",
  )
  const assistantUrl = "https://google.fr"
  backlinkTag.innerHTML = `
    Avant de jeter votre objet, demandez-lui !
    <a href="${assistantUrl}" target="_blank" rel="noreferrer" title="Ouvrir l'assistant au tri dans une nouvelle fenêtre">L'assistant au tri de l'ADEME</a> vous aide à choisir entre recyclage, réemploi ou mise à la poubelle en dernier recours.`
  iframe.insertAdjacentElement("afterend", backlinkTag)
}

function initScript() {
  const parts = [origin]
  const iframeResizerOptions: iframeResizer.IFramePageOptions = {
    license: "GPLv3",
    id: "quefairedemesdechets-assistant",
  }
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
  generateBackLink(iframe)
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
