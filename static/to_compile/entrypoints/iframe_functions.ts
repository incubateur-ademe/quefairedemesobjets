function compileIframeAttributes(
  baseUrl: string,
  urlParams: URLSearchParams,
  maxWidth: string,
  height: string,
  route: string
): { [Property in keyof HTMLIFrameElement]?: unknown } {
  return {
    src: `${baseUrl}/${route}?${urlParams.toString()}`,
    id: "lvao_iframe",
    frameBorder: "0",
    scrolling: "no",
    allow: "geolocation; clipboard-write",
    allowFullscreen: true,
    title: "Longue vie aux objets",
    style: `overflow: hidden; max-width: ${maxWidth}; width: 100%; height: ${height};`,
  }
}

function parseJSONDataset(dataset: string): any {
  try {
    return JSON.stringify(JSON.parse(dataset.replace(/'/g, '"')))
  } catch (error) {
    console.error("Failed to parse dataset:", error)
    return null
  }
}

export function buildAndInsertIframeFrom(
  iframeAttributes: object,
  iframeExtraAttributes: object,
  scriptTag: HTMLScriptElement,
) {
  const iframe = document.createElement("iframe")
  for (var key in iframeAttributes) {
    iframe.setAttribute(key, iframeAttributes[key])
  }
  for (var key in iframeExtraAttributes) {
    iframe.setAttribute(key, iframeExtraAttributes[key])
  }
  scriptTag.insertAdjacentElement("afterend", iframe)
}

export function getIframeAttributesAndExtra(
  scriptTag: HTMLScriptElement,
  baseRoute: string,
  options?: { maxWidth: string },
) {
  let maxWidth = options?.maxWidth || "100%"
  let height = "700px"
  let route = baseRoute
  const BASE_URL = new URL(scriptTag.getAttribute("src")!).origin
  const urlParams = new URLSearchParams()

  let iframeExtraAttributes: { [Property in keyof HTMLScriptElement]?: unknown } = {}

  for (const param in scriptTag.dataset) {
    if (param == "epci_codes" && scriptTag.dataset[param]?.includes(",")) {
      for (const value of scriptTag.dataset[param].split(",")) {
        urlParams.append(param, value)
      }
      continue
    }
    if (param === "max_width") {
      maxWidth = scriptTag.dataset[param]!
      continue
    }
    if (param === "height") {
      height = scriptTag.dataset[param]!
      continue
    }
    if (param === "iframe_attributes") {
      iframeExtraAttributes = JSON.parse(scriptTag.dataset[param]!)
      continue
    }
    if (param === "bounding_box") {
      urlParams.append(param, parseJSONDataset(scriptTag.dataset[param]!))
      continue
    }
    if (param === "slug") {
      route += `/${scriptTag.dataset[param]}`
      continue
    }
    urlParams.append(param, scriptTag.dataset[param]!)
  }

  const iframeAttributes = compileIframeAttributes(
    BASE_URL,
    urlParams,
    maxWidth,
    height,
    route
  )
  return [iframeAttributes, iframeExtraAttributes]
}
