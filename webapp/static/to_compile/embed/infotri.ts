import {
  buildAndInsertIframeFrom,
  getIframeAttributesAndExtra,
} from "../js/iframe_functions"

const setupIframe = () => {
  // Add iFrame just after the script tag
  const scriptTag = document.currentScript as HTMLScriptElement

  // Parse the config string into individual dataset attributes
  // This allows iframe_functions to process them uniformly
  const config = scriptTag?.dataset?.config || ""
  if (config) {
    const params = new URLSearchParams(config)
    // Transfer each param from config string to individual dataset attributes
    params.forEach((value, key) => {
      scriptTag.dataset[key] = value
    })
  }

  const [iframeAttributes, iframeExtraAttributes] = getIframeAttributesAndExtra(
    scriptTag,
    "infotri/embed",
    { useAutoHeight: true, iframeId: "infotri" },
  )

  buildAndInsertIframeFrom(iframeAttributes, iframeExtraAttributes, scriptTag, "", {
    useIframeResizer: true,
    resizerOptions: {
      id: "quefairedemesdechets-infotri",
    },
  })
}

setupIframe()
