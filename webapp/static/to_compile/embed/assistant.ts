import {
  buildAndInsertIframeFrom,
  getIframeAttributesAndExtra,
} from "../js/iframe_functions"

const setupIframe = () => {
  // Add iFrame just after the script tag
  const scriptTag = document.currentScript as HTMLScriptElement

  // Use "dechet" as base route, but if data-objet is present it will be appended
  const [iframeAttributes, iframeExtraAttributes] = getIframeAttributesAndExtra(
    scriptTag,
    "dechet",
    { useAutoHeight: true, iframeId: "assistant" },
  )

  buildAndInsertIframeFrom(
    iframeAttributes,
    iframeExtraAttributes,
    scriptTag,
    "assistant",
    {
      useIframeResizer: true,
      resizerOptions: {
        id: "assistant",
      },
    },
  )
}

setupIframe()
