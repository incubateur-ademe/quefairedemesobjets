const setupIframe = () => {
    // Add iFrame just after the script tag
    const scriptTag = document.currentScript as HTMLScriptElement
    const BASE_URL = new URL(scriptTag.getAttribute("src")!).origin

    const urlParams = new URLSearchParams()
    urlParams.append("iframe", "1")
    let maxWidth = "800px"
    let height = "100vh"
    let iframeExtraAttributes = {}
    for (const param in scriptTag.dataset) {
        if (param === "max_width") {
            maxWidth = scriptTag.dataset[param]
            continue
        }
        if (param === "height") {
            height = scriptTag.dataset[param]
            continue
        }
        if (param === "iframe_attributes") {
            iframeExtraAttributes = JSON.parse(scriptTag.dataset[param])
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
        allowfullscreen: true,
        webkitallowfullscreen: true,
        mozallowfullscreen: true,
        style: `overflow: hidden; max-width: ${maxWidth}; width: 100%; height: ${height};`,
    }
    for (var key in iframeAttributes) {
        iframe.setAttribute(key, iframeAttributes[key])
    }
    for (var key in iframeExtraAttributes) {
        iframe.setAttribute(key, iframeExtraAttributes[key])
    }
    scriptTag.insertAdjacentElement("afterend", iframe)
}

//addIframeResizer()
setupIframe()
