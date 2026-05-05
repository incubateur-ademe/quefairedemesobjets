import iframeResize from "@iframe-resizer/parent"
import { BacklinkKey, generateBackLink } from "../embed/helpers"
import { URL_PARAM_NAME_FOR_IFRAME_SCRIPT_MODE } from "./helpers"
import { getBaseUrlFromEnv } from "./url_utils"

// Constants
const DEFAULT_MAX_WIDTH = "100%"
const DEFAULT_HEIGHT = "100vh" // As recommended by iframe-resizer docs
const IFRAME_ID = "lvao_iframe"
// Distinct titles per route to satisfy RGAA 2.2 (each iframe must have a
// unique, descriptive title). Pages embedding several iframes can override
// per-iframe via the `data-title` attribute on the script tag.
const IFRAME_TITLES: Record<string, string> = {
  carte: "Carte Longue Vie aux Objets — Où réparer ou déposer mon objet",
  formulaire:
    "Longue Vie aux Objets — Formulaire de recherche de solutions de réemploi",
  infotri: "Info-tri — Configurateur de consignes de tri",
  assistant: "Que faire de mes objets et déchets — Assistant de recherche",
}
const IFRAME_TITLE_FALLBACK = "Que faire de mes objets et déchets"

// Special dataset attributes that require custom handling
const SPECIAL_ATTRIBUTES = {
  testid: "testid",
  debugReferrer: "debugReferrer",
  objet: "objet",
  slug: "slug",
  epciCodes: "epci_codes",
  maxWidth: "max_width",
  height: "height",
  iframeAttributes: "iframe_attributes",
  boundingBox: "bounding_box",
  title: "title",
} as const

/**
 * Configuration options for iframe setup
 */
interface IframeSetupOptions {
  maxWidth?: string
  height?: string
  useAutoHeight?: boolean
  addScriptModeParam?: boolean
  iframeId?: string
}

/**
 * Configuration options for iframe-resizer library
 */
interface IframeResizerOptions {
  id?: string
  license?: string
  checkOrigin?: boolean
  log?: boolean | "expanded" | "collapsed" | number
}

/**
 * Options for building and inserting an iframe
 */
interface BuildIframeOptions {
  useIframeResizer?: boolean
  resizerOptions?: IframeResizerOptions
}

/**
 * Parses a JSON string from dataset attribute, replacing single quotes with double quotes
 */
function parseDatasetJSON(dataset: string): string | null {
  try {
    return JSON.stringify(JSON.parse(dataset.replace(/'/g, '"')))
  } catch (error) {
    console.error("Failed to parse dataset:", error)
    return null
  }
}

/**
 * Captures the full referrer URL including path and query parameters.
 * Returns the complete URL of the parent page.
 */
function captureFullReferrer(): string {
  // Get the full current URL including pathname and search params
  return window.location.href
}

/**
 * Resolves the iframe title in priority order:
 * 1. Author-provided `data-title` on the script tag
 * 2. Route-specific default
 * 3. Generic fallback
 */
function resolveIframeTitle(route: string, customTitle?: string): string {
  if (customTitle) return customTitle
  // Route may include a sub-path like "carte/cyclevia"; only the prefix matters.
  const baseRoute = route.split("/")[0]
  return IFRAME_TITLES[baseRoute] || IFRAME_TITLE_FALLBACK
}

/**
 * Creates iframe HTML attributes configuration
 */
function createIframeAttributes(
  baseUrl: string,
  urlParams: URLSearchParams,
  maxWidth: string,
  height: string,
  route: string,
  useAutoHeight: boolean,
  iframeId?: string,
  customTitle?: string,
): Record<string, any> {
  return {
    src: `${baseUrl}/${route}?${urlParams.toString()}`,
    id: iframeId || IFRAME_ID,
    frameBorder: "0",
    scrolling: "no",
    allow: "geolocation; clipboard-write",
    allowFullscreen: true,
    title: resolveIframeTitle(route, customTitle),
    style: `overflow: hidden; max-width: ${maxWidth}; width: 100%; height: ${height};`,
  }
}

/**
 * Processes dataset attributes from script tag.
 * Returns processed route, URL params, iframe attributes, and dimensions.
 */
function processDatasetAttributes(
  scriptTag: HTMLScriptElement,
  baseRoute: string,
  options: IframeSetupOptions,
): {
  route: string
  urlParams: URLSearchParams
  iframeExtraAttributes: Record<string, string>
  maxWidth: string
  height: string
  customTitle?: string
} {
  let route = baseRoute
  let maxWidth = options.maxWidth || DEFAULT_MAX_WIDTH
  let height = options.height || DEFAULT_HEIGHT
  let customTitle: string | undefined
  const urlParams = new URLSearchParams()
  const iframeExtraAttributes: Record<string, string> = {}

  // Add standard query parameters based on options
  if (options.addScriptModeParam) {
    urlParams.set(URL_PARAM_NAME_FOR_IFRAME_SCRIPT_MODE, "1")
  }

  // Capture the full referrer URL and pass it as a URL parameter (base64 encoded)
  // This allows the analytics controller to track the parent page URL including query params
  const fullReferrer = captureFullReferrer()
  const encodedReferrer = btoa(fullReferrer)
  urlParams.set("ref", encodedReferrer)

  // Process all dataset attributes in a single loop
  for (const [key, value] of Object.entries(scriptTag.dataset)) {
    if (!value) continue

    switch (key) {
      // Special handling for test IDs
      case SPECIAL_ATTRIBUTES.testid:
        iframeExtraAttributes["data-testid"] = value
        break

      // Special handling for debug mode
      case SPECIAL_ATTRIBUTES.debugReferrer:
        iframeExtraAttributes["referrerPolicy"] = "no-referrer"
        break

      // Route extensions (slug or objet)
      case SPECIAL_ATTRIBUTES.slug:
      case SPECIAL_ATTRIBUTES.objet:
        route += `/${value}`
        break

      // Dimension overrides
      case SPECIAL_ATTRIBUTES.maxWidth:
        maxWidth = value
        break

      case SPECIAL_ATTRIBUTES.height:
        height = value
        break

      // Custom title — never propagated to URL params, only used as iframe attribute
      case SPECIAL_ATTRIBUTES.title:
        customTitle = value
        break

      // Complex attribute handling
      case SPECIAL_ATTRIBUTES.epciCodes:
        if (value.includes(",")) {
          value.split(",").forEach((code) => urlParams.append(key, code))
        } else {
          urlParams.append(key, value)
        }
        break

      case SPECIAL_ATTRIBUTES.iframeAttributes:
        Object.assign(iframeExtraAttributes, JSON.parse(value))
        break

      case SPECIAL_ATTRIBUTES.boundingBox:
        const parsed = parseDatasetJSON(value)
        if (parsed) {
          urlParams.append(key, parsed)
        }
        break

      // Default: add as URL query parameter
      default:
        urlParams.append(key, value)
    }
  }

  return { route, urlParams, iframeExtraAttributes, maxWidth, height, customTitle }
}

/**
 * Applies attributes to an iframe element
 */
function applyAttributesToIframe(
  iframe: HTMLIFrameElement,
  attributes: Record<string, string>,
  extraAttributes: Record<string, string>,
): void {
  for (const [key, value] of Object.entries(attributes)) {
    iframe.setAttribute(key, value)
  }
  for (const [key, value] of Object.entries(extraAttributes)) {
    iframe.setAttribute(key, value)
  }
}

/**
 * Initializes iframe-resizer on the iframe element.
 * Uses a unique ID to prevent conflicts when multiple iframes are on the same page.
 */
function initializeIframeResizer(
  iframe: HTMLIFrameElement,
  options?: IframeResizerOptions,
): void {
  // Generate a unique ID if not provided
  const iframeId = options?.id || `iframe-${Math.random().toString(36).substr(2, 9)}`

  iframe.onload = () => {
    iframeResize(
      {
        license: "GPLv3",
        checkOrigin: false,
        log: false,
        ...options,
        // Override with unique ID to prevent conflicts
        id: iframeId,
      },
      iframe,
    )
  }
}

/**
 * Builds iframe element and inserts it after the script tag.
 * Also generates and inserts backlink.
 */
export async function buildAndInsertIframeFrom(
  iframeAttributes: Record<string, string>,
  iframeExtraAttributes: Record<string, string>,
  scriptTag: HTMLScriptElement,
  backlinkKey?: BacklinkKey,
  options?: BuildIframeOptions,
): Promise<void> {
  const iframe = document.createElement("iframe")
  const baseUrl = getBaseUrlFromEnv()

  // Apply all attributes
  applyAttributesToIframe(iframe, iframeAttributes, iframeExtraAttributes)

  // Insert iframe after script tag
  scriptTag.insertAdjacentElement("afterend", iframe)

  // Notify the iframe when it enters the parent page's viewport.
  // The analytics controller inside the iframe listens for this message
  // to fire the iframe_page_viewed event exactly once.
  const observer = new IntersectionObserver(
    (entries, obs) => {
      if (entries[0].intersectionRatio > 0) {
        iframe.contentWindow?.postMessage({ type: "iframe_in_viewport" }, "*")
        obs.disconnect()
      }
    },
    { threshold: 0.01 },
  )
  observer.observe(iframe)

  // Generate and insert backlink
  await generateBackLink(iframe, backlinkKey, baseUrl)

  // Initialize iframe-resizer if requested
  if (options?.useIframeResizer) {
    initializeIframeResizer(iframe, options.resizerOptions)
  }
}

/**
 * Extracts iframe attributes and extra attributes from script tag dataset.
 * Returns a tuple of [iframe attributes, extra attributes].
 */
export function getIframeAttributesAndExtra(
  scriptTag: HTMLScriptElement,
  baseRoute: string,
  options: IframeSetupOptions = {},
): [Record<string, string>, Record<string, string>] {
  const baseUrl = getBaseUrlFromEnv()

  // Process all dataset attributes
  const { route, urlParams, iframeExtraAttributes, maxWidth, height, customTitle } =
    processDatasetAttributes(scriptTag, baseRoute, options)

  // Create iframe attributes
  const iframeAttributes = createIframeAttributes(
    baseUrl,
    urlParams,
    maxWidth,
    height,
    route,
    options.useAutoHeight || false,
    options.iframeId,
    customTitle,
  )

  return [iframeAttributes, iframeExtraAttributes]
}
