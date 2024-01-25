import { iframeResize } from "iframe-resizer"
import "iframe-resizer/js/iframeResizer.contentWindow"
const addIframeResizer = () => {
    // Add iframeResizer.min.js to the head
    const head = document.head
    const script1 = document.createElement("script")
    script1.src =
        "https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.6/iframeResizer.min.js"
    script1.integrity =
        "sha512-f0wd6UIvZbsjPNebGx+uMzHmg6KXr1jWvumJDYSEDmwYJYOptZ0dTka/wBJu7Tj80tnCYMKoKicqvZiIc9GJgw=="
    script1.crossOrigin = "anonymous"
    script1.referrerPolicy = "no-referrer"
    head.appendChild(script1)
}

const setupIframe = () => {
    // Add iFrame just after the script tag
    const scriptTag = document.getElementById("lvao_script")
    const urlParams = scriptTag.dataset.params
        ? new URLSearchParams(JSON.parse(scriptTag.dataset.params))
        : new URLSearchParams()
    urlParams.append("iframe", "1")
    const baseUrl = "https://longuevieauxobjets.ademe.fr"
    const iframe = document.createElement("iframe")
    iframe.src = `${baseUrl}?${urlParams.toString()}`
    iframe.id = "lvao_iframe"
    iframe.setAttribute("frameborder", "0")
    iframe.setAttribute("scrolling", "no")
    iframe.setAttribute("allow", "geolocation")
    iframe.style.width = "100%"

    scriptTag.insertAdjacentElement("afterend", iframe)

    // Add iFrameResize script to the end of the body
    const body = document.body
    const script2 = document.createElement("script")
    script2.textContent = `
    document.getElementById('lvao_iframe').addEventListener('load', function () {
        iFrameResize({
            heightCalculationMethod: 'bodyScroll',
            maxWidth: 1000,
        }, '#lvao_iframe')
    });
`
    //    body.appendChild(script2)
    iframeResize(
        {
            heightCalculationMethod: "bodyScroll",
            maxWidth: 1000,
        },
        iframe,
    )
}

//addIframeResizer()
setupIframe()
