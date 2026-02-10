import {
  DetectedIframe,
  Warning,
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
} from "../../types"

function getIframeType(src: string): { type: DetectedIframe["type"]; slug?: string } {
  try {
    const url = new URL(src)
    const pathname = url.pathname

    // Assistant / Formulaire / Dechet
    if (
      pathname.startsWith(`/${FORMULAIRE_ROUTE}`) ||
      pathname.startsWith(`/${DECHET_ROUTE}`)
    ) {
      return { type: "assistant" }
    }

    // Carte: route is /carte or /carte/<slug>
    if (pathname.startsWith(`/${CARTE_ROUTE}`)) {
      const match = pathname.match(new RegExp(`^/${CARTE_ROUTE}/(.+)`))
      if (match) {
        const slug = match[1].replace(/\/$/, "")
        return { type: "carte_sur_mesure", slug }
      }
      return { type: "carte" }
    }

    return { type: "unknown" }
  } catch {
    return { type: "unknown" }
  }
}

function getDomain(src: string): string {
  try {
    return new URL(src).hostname
  } catch {
    return ""
  }
}

function isKnownDomain(domain: string): boolean {
  return KNOWN_DOMAINS.some((d) => domain === d || domain.endsWith("." + d))
}

function findAdjacentScript(iframe: HTMLIFrameElement): HTMLScriptElement | null {
  // Check previous sibling
  let sibling = iframe.previousElementSibling
  while (sibling) {
    if (sibling.tagName === "SCRIPT") {
      const src = sibling.getAttribute("src") || ""
      if (isKnownDomain(getDomain(src))) {
        return sibling as HTMLScriptElement
      }
    }
    // Only skip backlink divs
    if (sibling.tagName !== "DIV") break
    sibling = sibling.previousElementSibling
  }

  // Check next sibling
  sibling = iframe.nextElementSibling
  while (sibling) {
    if (sibling.tagName === "SCRIPT") {
      const src = sibling.getAttribute("src") || ""
      if (isKnownDomain(getDomain(src))) {
        return sibling as HTMLScriptElement
      }
    }
    if (sibling.tagName !== "DIV") break
    sibling = sibling.nextElementSibling
  }

  return null
}

function getDataAttributes(el: HTMLElement): Record<string, string> {
  const attrs: Record<string, string> = {}
  for (const attr of Array.from(el.attributes)) {
    if (
      attr.name.startsWith("data-") &&
      attr.name !== "data-testid" &&
      !attr.name.startsWith("data-qfdmo-")
    ) {
      attrs[attr.name] = attr.value
    }
  }
  return attrs
}

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

/**
 * Checks if a specific iframe has iframe-resizer attached.
 * Reads the data attribute set by the injected probe.
 */
function detectIframeResizerOnIframe(iframe: HTMLIFrameElement): boolean {
  // Check per-iframe probe result
  if (iframe.getAttribute("data-qfdmo-has-iframe-resizer") === "true") return true

  // Check global probe result (UMD fallback)
  if (
    document.documentElement.getAttribute("data-qfdmo-iframe-resizer-global") === "true"
  )
    return true

  // Fallback: check if carte.js or iframe.js scripts are present (they bundle iframe-resizer)
  const scripts = document.querySelectorAll("script")
  for (const script of scripts) {
    const src = script.getAttribute("src") || ""
    if (
      (src.includes(CARTE_SCRIPT_FILENAME) ||
        src.includes(FORMULAIRE_SCRIPT_FILENAME)) &&
      isKnownDomain(getDomain(src))
    ) {
      return true
    }
  }

  return false
}

function processIframe(
  iframe: HTMLIFrameElement,
  insideTemplate: boolean,
): DetectedIframe | null {
  const src = iframe.getAttribute("src") || ""
  const domain = getDomain(src)

  if (!isKnownDomain(domain)) return null

  const { type, slug } = getIframeType(src)
  const adjacentScript = insideTemplate ? null : findAdjacentScript(iframe)
  const hasAdjacentScript = adjacentScript !== null
  const scriptDataAttributes = adjacentScript ? getDataAttributes(adjacentScript) : {}
  const iframeDataAttributes = getDataAttributes(iframe)
  const hasIframeResizer = insideTemplate ? false : detectIframeResizerOnIframe(iframe)

  const warnings: Warning[] = []

  if (insideTemplate) {
    warnings.push({
      message:
        "Iframe cachee dans un element <template> (DOM virtuel / consent cookie) - non chargee tant que l'utilisateur n'a pas accepte",
      severity: "info",
    })
  }

  if (!hasAdjacentScript) {
    warnings.push({
      message:
        "Iframe incluse sans script adjacent - l'inclusion par script est recommandee",
      severity: "warning",
    })
  }

  if (type === "assistant" && !hasIframeResizer) {
    warnings.push({
      message:
        "iframe-resizer non detecte - le redimensionnement automatique ne fonctionnera pas",
      severity: "warning",
    })
  }

  if (domain !== MAIN_DOMAIN) {
    warnings.push({
      message: `Domaine "${domain}" utilise au lieu du domaine principal "${MAIN_DOMAIN}"`,
      severity: "warning",
    })
  }

  if (type === "carte" && Object.keys(scriptDataAttributes).length > 0) {
    warnings.push({
      message:
        "Carte avec des data-attributes sans slug - envisagez d'utiliser une carte sur mesure pour une meilleure gestion",
      severity: "info",
    })
  }

  return {
    src,
    domain,
    type:
      type === "carte" && Object.keys(scriptDataAttributes).length > 0
        ? "carte_preconfiguree"
        : type,
    slug,
    hasAdjacentScript,
    scriptSrc: adjacentScript?.getAttribute("src") || undefined,
    scriptDataAttributes,
    iframeDataAttributes,
    hasIframeResizer,
    insideTemplate,
    warnings,
  }
}

function isQfdmoPage(): boolean {
  return isKnownDomain(window.location.hostname)
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

function collectIframes(): DetectedIframe[] {
  const detected: DetectedIframe[] = []

  // Inject probe to check iframe-resizer on all iframes
  injectIframeResizerProbe()

  // Scan live DOM iframes
  const liveIframes = document.querySelectorAll("iframe")
  for (const iframe of liveIframes) {
    const result = processIframe(iframe, false)
    if (result) detected.push(result)
  }

  // Scan iframes hidden inside <template> elements (cookie consent / virtual DOM)
  const templates = document.querySelectorAll("template")
  for (const template of templates) {
    const templateIframes = template.content.querySelectorAll("iframe")
    for (const iframe of templateIframes) {
      const result = processIframe(iframe as HTMLIFrameElement, true)
      if (result) detected.push(result)
    }
  }

  return detected
}

function buildAnalysis(detected: DetectedIframe[]): PageAnalysis {
  return {
    iframes: detected,
    totalWarnings: detected.reduce((sum, iframe) => sum + iframe.warnings.length, 0),
    sessionStorage: readSessionStorage(),
    isQfdmoPage: isQfdmoPage(),
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "ANALYZE_PAGE") {
    // Return results immediately (synchronous)
    const detected = collectIframes()
    sendResponse(buildAnalysis(detected))
  }
  return true
})
