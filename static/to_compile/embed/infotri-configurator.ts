import {
  buildAndInsertIframeFrom,
  getIframeAttributesAndExtra,
} from "../js/iframe_functions"

const setupIframe = () => {
  // Add iFrame just after the script tag
  const scriptTag = document.currentScript as HTMLScriptElement
  const [iframeAttributes, iframeExtraAttributes] = getIframeAttributesAndExtra(
    scriptTag,
    "infotri",
    { useAutoHeight: true, iframeId: "infotri-configurator" },
  )
  buildAndInsertIframeFrom(
    iframeAttributes,
    iframeExtraAttributes,
    scriptTag,
    "infotri-configurator",
    {
      useIframeResizer: true,
      resizerOptions: {
        id: "infotri-configurator",
      },
    },
  )
}

setupIframe()
