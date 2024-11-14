import {
    buildAndInsertIframeFrom,
    getIframeAttributesAndExtra,
} from "./iframe_functions"

const setupIframe = () => {
    // Add iFrame just after the script tag
    const scriptTag = document.currentScript as HTMLScriptElement
    const [iframeAttributes, iframeExtraAttributes] = getIframeAttributesAndExtra(
        ["iframe", "1"],
        scriptTag,
        { maxWidth: "800px" },
    )
    buildAndInsertIframeFrom(iframeAttributes, iframeExtraAttributes, scriptTag)
}

setupIframe()
