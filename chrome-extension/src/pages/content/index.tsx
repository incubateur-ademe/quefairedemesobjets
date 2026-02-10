import {
  DetectedIframe,
  Warning,
  PageAnalysis,
  SessionStorageData,
  KNOWN_DOMAINS,
  MAIN_DOMAIN,
  CARTE_ROUTE,
  FORMULAIRE_ROUTE,
  FORMULAIRE_SCRIPT_FILENAME,
  SESSION_STORAGE_KEYS,
} from "../../types"

function getIframeType(src: string): { type: DetectedIframe["type"]; slug?: string } {
  try {
    const url = new URL(src)
    const pathname = url.pathname

    // Assistant / Formulaire
    if (pathname.startsWith(`/${FORMULAIRE_ROUTE}`)) {
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
    if (attr.name.startsWith("data-") && attr.name !== "data-testid") {
      attrs[attr.name] = attr.value
    }
  }
  return attrs
}

/**
 * Detects iframe-resizer by injecting a script into the page context.
 * Content scripts run in an isolated world and can't access page JS globals,
 * so we inject a small inline script that checks window.iFrameResize
 * and stores the result in a data attribute on <html>.
 */
function detectIframeResizer(): boolean {
  // Check the result from our injected probe
  const probeResult = document.documentElement.getAttribute("data-qfdmo-iframe-resizer")
  if (probeResult === "true") return true

  // Fallback: check script src attributes
  const scripts = document.querySelectorAll("script")
  for (const script of scripts) {
    const src = script.getAttribute("src") || ""
    if (src.includes(FORMULAIRE_SCRIPT_FILENAME) && isKnownDomain(getDomain(src))) {
      return true
    }
  }

  return false
}

/**
 * Injects a probe script into the page context to check for window.iFrameResize.
 * The result is written to a data attribute on <html> so the content script can read it.
 */
function injectIframeResizerProbe(): void {
  const script = document.createElement("script")
  script.textContent = `document.documentElement.setAttribute("data-qfdmo-iframe-resizer", typeof window.iFrameResize !== "undefined" ? "true" : "false");`
  document.documentElement.appendChild(script)
  script.remove()
}

function processIframe(
  iframe: HTMLIFrameElement,
  insideTemplate: boolean,
  globalIframeResizerDetected: boolean,
): DetectedIframe | null {
  const src = iframe.getAttribute("src") || ""
  const domain = getDomain(src)

  if (!isKnownDomain(domain)) return null

  const { type, slug } = getIframeType(src)
  const adjacentScript = insideTemplate ? null : findAdjacentScript(iframe)
  const hasAdjacentScript = adjacentScript !== null
  const scriptDataAttributes = adjacentScript ? getDataAttributes(adjacentScript) : {}
  const iframeDataAttributes = getDataAttributes(iframe)
  const hasIframeResizer = globalIframeResizerDetected

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

function analyzePage(): PageAnalysis {
  const detected: DetectedIframe[] = []
  injectIframeResizerProbe()
  const globalIframeResizerDetected = detectIframeResizer()

  // Scan live DOM iframes
  const liveIframes = document.querySelectorAll("iframe")
  for (const iframe of liveIframes) {
    const result = processIframe(iframe, false, globalIframeResizerDetected)
    if (result) detected.push(result)
  }

  // Scan iframes hidden inside <template> elements (cookie consent / virtual DOM)
  const templates = document.querySelectorAll("template")
  for (const template of templates) {
    const templateIframes = template.content.querySelectorAll("iframe")
    for (const iframe of templateIframes) {
      const result = processIframe(
        iframe as HTMLIFrameElement,
        true,
        globalIframeResizerDetected,
      )
      if (result) detected.push(result)
    }
  }

  return {
    iframes: detected,
    totalWarnings: detected.reduce((sum, iframe) => sum + iframe.warnings.length, 0),
    sessionStorage: readSessionStorage(),
    isQfdmoPage: isQfdmoPage(),
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "ANALYZE_PAGE") {
    const analysis = analyzePage()
    sendResponse(analysis)
  }
  return true
})
