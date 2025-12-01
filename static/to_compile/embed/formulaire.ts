import {
  buildAndInsertIframeFrom,
  getIframeAttributesAndExtra,
} from "../js/iframe_functions"

const setupIframe = () => {
  // Add iFrame just after the script tag
  const scriptTag = document.currentScript as HTMLScriptElement
  const [iframeAttributes, iframeExtraAttributes] = getIframeAttributesAndExtra(
    scriptTag,
    "formulaire",
    { maxWidth: "800px", iframeId: "formulaire" },
  )
  buildAndInsertIframeFrom(
    iframeAttributes,
    iframeExtraAttributes,
    scriptTag,
    "formulaire",
  )
}

setupIframe()
