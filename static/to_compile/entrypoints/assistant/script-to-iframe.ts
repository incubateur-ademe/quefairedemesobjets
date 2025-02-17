import { iframeResize } from "iframe-resizer";

const script = document.currentScript as HTMLScriptElement
const slug = script?.dataset?.objet;
const origin = new URL(script?.getAttribute("src")).origin

function initScript() {
  const parts = [origin]
  if (slug) {
    parts.push("dechet", slug)
  }
  parts.push("?iframe")
  const src = parts.join("/")

  const iframe = document.createElement("iframe");
  const iframeAttributes = {
    src,
    style: "border: none; width: 100%; display: block; margin: 0 auto;",
    allowfullscreen: true,
    allow: "geolocation; clipboard-write",
    title: "Que faire de mes objets et déchets"
  };

  if (script?.dataset?.testid) {
    iframeAttributes["data-testid"] = script.dataset.testid
  }

  const debugReferrer = typeof script?.dataset?.debugReferrer !== "undefined"
  if (debugReferrer) {
    iframeAttributes.referrerPolicy = "no-referrer"
  }
  for (var key in iframeAttributes) {
    iframe.setAttribute(key, iframeAttributes[key]);
  }

  script.parentNode?.insertBefore(iframe, script);
  iframe.onload = () => {
    iframeResize({}, iframe)
  }
}
if (document.readyState === "loading") {
  // Loading hasn't finished yet
  document.addEventListener("DOMContentLoaded", initScript);
} else {
  // `DOMContentLoaded` has already fired
  initScript();
}
