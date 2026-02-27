import {
  PageAnalysis,
  SessionStorageData,
  KNOWN_DOMAINS,
  MAIN_DOMAIN,
  CARTE_ROUTE,
  FORMULAIRE_ROUTE,
  DECHET_ROUTE,
  CARTE_SCRIPT_FILENAME,
  FORMULAIRE_SCRIPT_FILENAME,
  SESSION_STORAGE_KEYS,
  detectIframeIntegrations,
  buildDetectionConfig,
} from "../../types"

const detectionConfig = buildDetectionConfig({
  KNOWN_DOMAINS,
  MAIN_DOMAIN,
  CARTE_ROUTE,
  FORMULAIRE_ROUTE,
  DECHET_ROUTE,
  CARTE_SCRIPT_FILENAME,
  FORMULAIRE_SCRIPT_FILENAME,
})

// -- Chrome-specific: iframe-resizer probe --

/**
 * Injects a probe script that checks if a specific iframe has been processed
 * by iframe-resizer. When iframe-resizer v5 processes an iframe, it sets
 * `iframe.iframeResizer` (and `iframe.iFrameResizer`) as an API object
 * directly on the DOM element. Since content scripts run in an isolated world,
 * we inject into the page context to check these properties.
 *
 * Results are stored as data attributes on each iframe so the content script
 * can read them.
 */
function injectIframeResizerProbe(): void {
  const script = document.createElement("script")
  script.textContent = `
    (function() {
      var iframes = document.querySelectorAll("iframe");
      for (var i = 0; i < iframes.length; i++) {
        var iframe = iframes[i];
        var hasResizer = !!(iframe.iframeResizer || iframe.iFrameResizer);
        iframe.setAttribute("data-qfdmo-has-iframe-resizer", hasResizer ? "true" : "false");
      }
      // Also check for global (UMD fallback)
      var hasGlobal = (typeof window.iFrameResize !== "undefined") || (typeof window.iframeResize !== "undefined");
      document.documentElement.setAttribute("data-qfdmo-iframe-resizer-global", hasGlobal ? "true" : "false");
    })();
  `
  document.documentElement.appendChild(script)
  script.remove()
}

// -- Chrome-specific: session storage & page detection --

function isQfdmoPage(): boolean {
  return KNOWN_DOMAINS.some(
    (d) =>
      window.location.hostname === d ||
      window.location.hostname.endsWith("." + d),
  )
}

function readSessionStorage(): SessionStorageData | null {
  if (!isQfdmoPage()) return null

  try {
    const data = {} as SessionStorageData
    for (const key of SESSION_STORAGE_KEYS) {
      data[key] = sessionStorage.getItem(key)
    }
    return data
  } catch {
    return null
  }
}

// -- Analysis --

function buildAnalysis(): PageAnalysis {
  // Inject probe first so shared detection can read data attributes
  injectIframeResizerProbe()

  const iframes = detectIframeIntegrations(detectionConfig)

  return {
    iframes,
    totalWarnings: iframes.reduce(
      (sum, iframe) => sum + iframe.warnings.length,
      0,
    ),
    sessionStorage: readSessionStorage(),
    isQfdmoPage: isQfdmoPage(),
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "ANALYZE_PAGE") {
    sendResponse(buildAnalysis())
  }
  return true
})
