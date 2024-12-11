import { iframeResize } from "iframe-resizer";

window.addEventListener("DOMContentLoaded", () => {
  const script = document.getElementById("quefairedemesdechets");
  const search = script?.dataset?.search;
  const origin = new URL(script?.getAttribute("src")).origin
  const src = `${origin}/dechet/?iframe`;
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
})
