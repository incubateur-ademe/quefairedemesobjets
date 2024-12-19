import { iframeResize } from "iframe-resizer";

const script = document.currentScript as HTMLScriptElement
const slug = script?.dataset?.objet;
const origin = new URL(script?.getAttribute("src")).origin
const src = `${origin}/dechet/${slug || ''}?iframe`;
const iframe = document.createElement("iframe");

const iframeAttributes = {
  src,
  style: "border: none; width: 100%; display: block; margin: 0 auto;",
  allowfullscreen: true,
  allow: "geolocation; clipboard-write",
};

if (script?.dataset?.testid) {
  iframeAttributes["data-testid"] = script.dataset.testid
}

document.addEventListener("DOMContentLoaded", () => {

  const debugReferrer = typeof script?.dataset?.debugReferrer !== "undefined"
  if (debugReferrer) {
    iframeAttributes.referrerPolicy = "no-referrer"
  }
  for (var key in iframeAttributes) {
    iframe.setAttribute(key, iframeAttributes[key]);
  }

  iframeResize({}, iframe);

  script.parentNode.insertBefore(iframe, script);
});
