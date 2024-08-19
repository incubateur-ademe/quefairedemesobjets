import {
    buildAndInsertIframeFrom,
    getIframeAttributesAndExtra,
} from "./iframe_functions"

const setupIframe = () => {
    // Add iFrame just after the script tag
    const scriptTag = document.currentScript as HTMLScriptElement
    const [iframeAttributes, iframeExtraAttributes] = getIframeAttributesAndExtra(
        ["carte", "1"],
        scriptTag,
    )
    buildAndInsertIframeFrom(iframeAttributes, iframeExtraAttributes, scriptTag)
}

//addIframeResizer()
setupIframe()
