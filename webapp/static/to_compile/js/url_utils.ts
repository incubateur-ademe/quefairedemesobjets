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
