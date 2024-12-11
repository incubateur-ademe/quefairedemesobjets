import { iframeResize } from "iframe-resizer";

window.addEventListener("DOMContentLoaded", () => {
  const script = document.getElementById("quefairedemesdechets");
  const search = script?.dataset?.search;
  const source = window.location.href.toString();

  const src = `http://localhost:8000/dechet${
    search || "?"
  }&iframe=1&source=${source}`;

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
