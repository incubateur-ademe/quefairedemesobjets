import {
  buildAndInsertIframeFrom,
  getIframeAttributesAndExtra,
} from "../js/iframe_functions"

const setupIframe = () => {
  // Add iFrame just after the script tag
  const scriptTag = document.currentScript as HTMLScriptElement
  const [iframeAttributes, iframeExtraAttributes] = getIframeAttributesAndExtra(
    scriptTag,
    "carte",
    { maxWidth: "100%", height: "700px", iframeId: "carte" },
  )
  buildAndInsertIframeFrom(iframeAttributes, iframeExtraAttributes, scriptTag, "carte")
}

setupIframe()
