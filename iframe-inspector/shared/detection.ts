/**
 * Shared detection logic for QFDMO iframe/script integrations.
 * Used by:
 *   - Chrome extension content script (runs in isolated world)
 *   - Batch check script via Playwright's page.evaluate()
 *
 * IMPORTANT: detectIframeIntegrations() and detectScriptIntegrations() are
 * self-contained functions. All helpers are defined inside the function body
 * so they can be serialized and passed to page.evaluate() without closures.
 * They must NOT reference any module-level variables.
 */

// -- Types (erased at runtime, safe to define at module level) --

export interface DetectionConfig {
  knownDomains: readonly string[];
  mainDomain: string;
  carteRoute: string;
  formulaireRoute: string;
  dechetRoute: string;
  carteScriptFilename: string;
  formulaireScriptFilename: string;
}

export type IframeType =
  | "carte"
  | "carte_sur_mesure"
  | "carte_preconfiguree"
  | "assistant"
  | "unknown";

export interface IntegrationWarning {
  message: string;
  severity: "error" | "warning" | "info";
}

export interface DetectedIframe {
  src: string;
  domain: string;
  type: IframeType;
  slug?: string;
  hasAdjacentScript: boolean;
  scriptSrc?: string;
  scriptDataAttributes: Record<string, string>;
  iframeDataAttributes: Record<string, string>;
  hasIframeResizer: boolean;
  insideTemplate: boolean;
  warnings: IntegrationWarning[];
}

export interface DetectedScript {
  src: string;
  domain: string;
  path: string;
  dataAttributes: Record<string, string>;
  urlParams: Record<string, string[]>;
}

// -- Detection functions (self-contained for page.evaluate) --

/**
 * Detects QFDMO iframe integrations on the current page.
 *
 * Self-contained: all helpers are defined inside, nothing is captured from
 * the enclosing module scope. Config is the only external input.
 */
export function detectIframeIntegrations(
  config: DetectionConfig,
): DetectedIframe[] {
  const {
    knownDomains,
    mainDomain,
    carteRoute,
    formulaireRoute,
    dechetRoute,
    carteScriptFilename,
    formulaireScriptFilename,
  } = config;

  function getDomain(src: string): string {
    try {
      return new URL(src).hostname;
    } catch {
      return "";
    }
  }

  function isKnownDomain(domain: string): boolean {
    return knownDomains.some((d) => domain === d || domain.endsWith("." + d));
  }

  function getIframeType(src: string): {
    type: IframeType;
    slug?: string;
  } {
    try {
      const url = new URL(src);
      const pathname = url.pathname;

      if (
        pathname.startsWith(`/${formulaireRoute}`) ||
        pathname.startsWith(`/${dechetRoute}`)
      ) {
        return { type: "assistant" };
      }

      if (pathname.startsWith(`/${carteRoute}`)) {
        const match = pathname.match(new RegExp(`^/${carteRoute}/(.+)`));
        if (match) {
          return {
            type: "carte_sur_mesure",
            slug: match[1].replace(/\/$/, ""),
          };
        }
        return { type: "carte" };
      }

      return { type: "unknown" };
    } catch {
      return { type: "unknown" };
    }
  }

  function getDataAttributes(el: Element): Record<string, string> {
    const attrs: Record<string, string> = {};
    for (const attr of Array.from(el.attributes)) {
      if (
        attr.name.startsWith("data-") &&
        attr.name !== "data-testid" &&
        !attr.name.startsWith("data-qfdmo-")
      ) {
        attrs[attr.name] = attr.value;
      }
    }
    return attrs;
  }

  function findAdjacentScript(iframe: Element): Element | null {
    // Check previous siblings (skip DIVs for backlink divs)
    let sibling = iframe.previousElementSibling;
    while (sibling) {
      if (sibling.tagName === "SCRIPT") {
        const src = sibling.getAttribute("src") || "";
        if (isKnownDomain(getDomain(src))) return sibling;
      }
      if (sibling.tagName !== "DIV") break;
      sibling = sibling.previousElementSibling;
    }

    // Check next siblings
    sibling = iframe.nextElementSibling;
    while (sibling) {
      if (sibling.tagName === "SCRIPT") {
        const src = sibling.getAttribute("src") || "";
        if (isKnownDomain(getDomain(src))) return sibling;
      }
      if (sibling.tagName !== "DIV") break;
      sibling = sibling.nextElementSibling;
    }

    return null;
  }

  function detectIframeResizer(iframe: Element): boolean {
    // Direct property check (works in page context: Playwright evaluate)
    if ((iframe as any).iframeResizer || (iframe as any).iFrameResizer) {
      return true;
    }

    // Data attribute check (works after Chrome extension probe injection)
    if (iframe.getAttribute("data-qfdmo-has-iframe-resizer") === "true") {
      return true;
    }

    // Global check (set by Chrome probe)
    if (
      document.documentElement.getAttribute(
        "data-qfdmo-iframe-resizer-global",
      ) === "true"
    ) {
      return true;
    }

    // Fallback: check if carte.js or iframe.js scripts are loaded
    const scripts = document.querySelectorAll("script");
    for (const script of scripts) {
      const src = script.getAttribute("src") || "";
      if (
        (src.includes(carteScriptFilename) ||
          src.includes(formulaireScriptFilename)) &&
        isKnownDomain(getDomain(src))
      ) {
        return true;
      }
    }

    return false;
  }

  function processIframe(
    iframe: Element,
    insideTemplate: boolean,
  ): DetectedIframe | null {
    const src = iframe.getAttribute("src") || "";
    const domain = getDomain(src);

    if (!isKnownDomain(domain)) return null;

    const { type, slug } = getIframeType(src);
    const adjacentScript = insideTemplate ? null : findAdjacentScript(iframe);
    const hasAdjacentScript = adjacentScript !== null;
    const scriptDataAttributes = adjacentScript
      ? getDataAttributes(adjacentScript)
      : {};
    const iframeDataAttributes = getDataAttributes(iframe);
    const hasIframeResizer = insideTemplate
      ? false
      : detectIframeResizer(iframe);

    const warnings: IntegrationWarning[] = [];

    if (insideTemplate) {
      warnings.push({
        message:
          "Iframe cachee dans un element <template> (DOM virtuel / consent cookie) - non chargee tant que l'utilisateur n'a pas accepte",
        severity: "info",
      });
    }

    if (!hasAdjacentScript) {
      warnings.push({
        message:
          "Iframe incluse sans script adjacent - l'inclusion par script est recommandee",
        severity: "warning",
      });
    }

    if (type === "assistant" && !hasIframeResizer) {
      warnings.push({
        message:
          "iframe-resizer non detecte - le redimensionnement automatique ne fonctionnera pas",
        severity: "warning",
      });
    }

    if (domain !== mainDomain) {
      warnings.push({
        message: `Domaine "${domain}" utilise au lieu du domaine principal "${mainDomain}"`,
        severity: "warning",
      });
    }

    if (type === "carte" && Object.keys(scriptDataAttributes).length > 0) {
      warnings.push({
        message:
          "Carte avec des data-attributes sans slug - envisagez d'utiliser une carte sur mesure pour une meilleure gestion",
        severity: "info",
      });
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
    };
  }

  // -- Main detection logic --

  const detected: DetectedIframe[] = [];

  // Scan live DOM iframes
  const liveIframes = document.querySelectorAll("iframe");
  for (const iframe of liveIframes) {
    const result = processIframe(iframe, false);
    if (result) detected.push(result);
  }

  // Scan iframes hidden inside <template> elements (cookie consent / virtual DOM)
  const templates = document.querySelectorAll("template");
  for (const template of templates) {
    const templateIframes = (
      template as HTMLTemplateElement
    ).content.querySelectorAll("iframe");
    for (const iframe of templateIframes) {
      const result = processIframe(iframe as Element, true);
      if (result) detected.push(result);
    }
  }

  return detected;
}

/**
 * Detects standalone script tags from known domains.
 * Self-contained for page.evaluate() compatibility.
 */
export function detectScriptIntegrations(
  config: DetectionConfig,
): DetectedScript[] {
  const { knownDomains } = config;

  function getDomain(src: string): string {
    try {
      return new URL(src).hostname;
    } catch {
      return "";
    }
  }

  function isKnownDomain(domain: string): boolean {
    return knownDomains.some((d) => domain === d || domain.endsWith("." + d));
  }

  const results: DetectedScript[] = [];
  const scripts = document.querySelectorAll("script[src]");

  for (const script of scripts) {
    const src = script.getAttribute("src") || "";
    const domain = getDomain(src);
    if (!isKnownDomain(domain)) continue;

    try {
      const url = new URL(src);
      const dataAttributes: Record<string, string> = {};
      for (const attr of Array.from(script.attributes)) {
        if (attr.name.startsWith("data-") && attr.name !== "data-testid") {
          dataAttributes[attr.name] = attr.value;
        }
      }
      const urlParams: Record<string, string[]> = {};
      url.searchParams.forEach((value, key) => {
        if (!urlParams[key]) urlParams[key] = [];
        urlParams[key].push(value);
      });

      results.push({
        src,
        domain,
        path: url.pathname,
        dataAttributes,
        urlParams,
      });
    } catch {
      /* skip invalid URLs */
    }
  }

  return results;
}

// -- Helper to build config from shared_constants --

export function buildDetectionConfig(constants: {
  KNOWN_DOMAINS: readonly string[];
  MAIN_DOMAIN: string;
  CARTE_ROUTE: string;
  FORMULAIRE_ROUTE: string;
  DECHET_ROUTE: string;
  CARTE_SCRIPT_FILENAME: string;
  FORMULAIRE_SCRIPT_FILENAME: string;
}): DetectionConfig {
  return {
    knownDomains: [...constants.KNOWN_DOMAINS],
    mainDomain: constants.MAIN_DOMAIN,
    carteRoute: constants.CARTE_ROUTE,
    formulaireRoute: constants.FORMULAIRE_ROUTE,
    dechetRoute: constants.DECHET_ROUTE,
    carteScriptFilename: constants.CARTE_SCRIPT_FILENAME,
    formulaireScriptFilename: constants.FORMULAIRE_SCRIPT_FILENAME,
  };
}
