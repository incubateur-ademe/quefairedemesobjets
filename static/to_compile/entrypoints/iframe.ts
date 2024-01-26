import { iframeResize } from "iframe-resizer"

const PUBLIC_WEBSITE_URL = process.env.PUBLIC_WEBSITE_URL || "http://localhost:8000"

const setupIframe = () => {
    // Add iFrame just after the script tag
    const scriptTag = document.currentScript as HTMLScriptElement
    const urlParams = new URLSearchParams()
    urlParams.append("iframe", "1")
    let maxWidth = 800
    for (const param in scriptTag.dataset) {
        if (param === "max_width") {
            maxWidth = parseInt(scriptTag.dataset[param])
            continue
        }
        urlParams.append(param, scriptTag.dataset[param])
        console.log(param, scriptTag.dataset[param])
    }

    const iframe = document.createElement("iframe")
    const iframeAttributes = {
        src: `${PUBLIC_WEBSITE_URL}?${urlParams.toString()}`,
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
            checkOrigin: [PUBLIC_WEBSITE_URL],
        },
        iframe,
    )
}

//addIframeResizer()
setupIframe()
