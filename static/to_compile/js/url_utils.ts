/**
 * Shared utility functions for handling URLs in iframe scripts.
 * This module provides a consistent way to extract and validate base URLs
 * from script tags, with proper fallback handling.
 */

/**
 * Get allowed hosts from environment variable.
 * Parses dynamically to support test mocking.
 */
function getAllowedHostsFromEnv(): string[] {
  return process.env.ALLOWED_HOSTS
    ? process.env.ALLOWED_HOSTS.split(",").map((h) => h.trim())
    : []
}

/**
 * Get base URL from environment variable.
 * Returns dynamically to support test mocking.
 */
function getBaseUrlFromEnv(): string {
  return process.env.BASE_URL || ""
}

/**
 * Extracts the origin (protocol + host) from a script tag's src attribute.
 * Handles protocol-relative URLs and validates against allowed hosts.
 *
 * @param scriptTag - The script element to extract the URL from
 *
 * Algorithm:
 * 1. Get the src attribute from the script tag
 * 2. If src is protocol-relative (starts with //), prepend https://
 * 3. Parse the URL to extract the origin
 * 4. Validate the hostname against ALLOWED_HOSTS
 * 5. Return the validated URL or fall back to BASE_URL from environment
 *
 * @example
 * // Script with absolute URL
 * <script src="https://example.com/script.js"></script>
 * getBaseUrlFromScript(scriptTag) // "https://example.com"
 *
 * @example
 * // Script with protocol-relative URL
 * <script src="//example.com/script.js"></script>
 * getBaseUrlFromScript(scriptTag) // "https://example.com"
 *
 * @example
 * // Script with invalid/untrusted URL
 * <script src="https://malicious.com/script.js"></script>
 * getBaseUrlFromScript(scriptTag) // Falls back to process.env.BASE_URL
 */
export function getBaseUrlFromScript(scriptTag: HTMLScriptElement | null): string {
  const baseUrl = getBaseUrlFromEnv()
  const allowedHosts = getAllowedHostsFromEnv()

  // If no script tag, return BASE_URL from environment
  if (!scriptTag) {
    console.warn("No script tag provided, using BASE_URL from environment")
    return baseUrl
  }

  const src = scriptTag.getAttribute("src")
  if (!src) {
    console.warn("Script tag has no src attribute, using BASE_URL from environment")
    return baseUrl
  }

  try {
    // Handle protocol-relative URLs by prepending https://
    const absoluteSrc = src.startsWith("//") ? `https:${src}` : src

    // Parse the URL to extract origin
    const url = new URL(absoluteSrc)
    const hostname = url.hostname

    // Validate against allowed hosts if configured
    if (allowedHosts.length > 0 && !allowedHosts.includes("*")) {
      const isAllowed = allowedHosts.some((allowedHost) => {
        // Exact match or wildcard subdomain match
        return hostname === allowedHost || hostname.endsWith(`.${allowedHost}`)
      })

      if (!isAllowed) {
        console.warn(
          `Hostname "${hostname}" not in ALLOWED_HOSTS, using BASE_URL from environment`,
        )
        return baseUrl
      }
    }

    // Return the validated origin
    return url.origin
  } catch (error) {
    console.error("Failed to parse script src as URL:", error)
    console.warn("Using BASE_URL from environment as fallback")
    return baseUrl
  }
}

/**
 * Legacy function for backward compatibility.
 * Extracts base URL from script tag with fallback to BASE_URL.
 *
 * @deprecated Use getBaseUrlFromScript instead for better error handling
 */
export function getBaseUrl(scriptTag: HTMLScriptElement | null): string {
  return getBaseUrlFromScript(scriptTag)
}
