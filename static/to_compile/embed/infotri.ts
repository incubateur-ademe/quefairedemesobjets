import iframeResize from "@iframe-resizer/parent"
import { iframeResizer } from "@iframe-resizer/child"
import { generateBackLink } from "./helpers"

const script = document.currentScript as HTMLScriptElement
const config = script?.dataset?.config || ""
let baseUrl = new URL(script?.getAttribute("src")).origin
// TODO: handle if not ademe domain

if (process.env.BASE_URL) {
  baseUrl = process.env.BASE_URL
}

async function initScript() {
  const parts = [baseUrl, "infotri", "embed"]
  const iframeResizerOptions: iframeResizer.IFramePageOptions = {
    license: "GPLv3",
    id: "quefairedemesdechets-infotri",
  }

  const searchParams = new URLSearchParams(config)
  searchParams.set("iframe", "")

  const src = `${parts.join("/")}?${searchParams.toString()}`
  const iframe = document.createElement("iframe")
  const iframeAttributes = {
    src,
    style: "border: none; width: 100%; height: auto; display: block; margin: 0 auto;",
    allowfullscreen: true,
    title: "Info-tri - Longue vie aux objets",
  }

  for (var key in iframeAttributes) {
    iframe.setAttribute(key, iframeAttributes[key])
  }

  script.parentNode?.insertBefore(iframe, script)
  const backlinkStyle =
    "font-family: system-ui; font-size: 18px; text-align: center; padding-top: 0.5rem;"
  await generateBackLink(iframe, "infotri", baseUrl, backlinkStyle)
  iframe.onload = () => {
    iframeResize(iframeResizerOptions, iframe)
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initScript)
} else {
  initScript()
}
