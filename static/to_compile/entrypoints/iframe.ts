import { iframeResize } from "iframe-resizer"

const setupIframe = () => {
    // Add iFrame just after the script tag
    const scriptTag = document.currentScript as HTMLScriptElement
    const BASE_URL = new URL(scriptTag.getAttribute("src")!).origin

    const urlParams = new URLSearchParams()
    urlParams.append("iframe", "1")
    let maxWidth = 800
    for (const param in scriptTag.dataset) {
        if (param === "max_width") {
            maxWidth = parseInt(scriptTag.dataset[param])
            continue
        }
        urlParams.append(param, scriptTag.dataset[param])
    }

    const iframe = document.createElement("iframe")
    const iframeAttributes = {
        src: `${BASE_URL}?${urlParams.toString()}`,
        id: "lvao_iframe",
        frameborder: "0",
        scrolling: "no",
        allow: "geolocation",
        style: "width: 100%",
        allowfullscreen: true,
        webkitallowfullscreen: true,
        mozallowfullscreen: true,
    }
    for (var key in iframeAttributes) {
        iframe.setAttribute(key, iframeAttributes[key])
    }
    scriptTag.insertAdjacentElement("afterend", iframe)

    iframeResize(
        {
            heightCalculationMethod: "bodyScroll",
            maxWidth: maxWidth,
            checkOrigin: [BASE_URL],
        },
        iframe,
    )
}

//addIframeResizer()
setupIframe()
