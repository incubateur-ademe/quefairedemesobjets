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

for (var key in iframeAttributes) {
  iframe.setAttribute(key, iframeAttributes[key]);
}

iframeResize({}, iframe);

script.parentNode.insertBefore(iframe, script);
