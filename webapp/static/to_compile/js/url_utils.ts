/**
 * Shared utility functions for handling URLs in iframe scripts.
 * This module provides a consistent way to extract and validate base URLs
 * from script tags, with proper fallback handling.
 */

/**
 * Get base URL from environment variable.
 * Returns dynamically to support test mocking.
 */
export function getBaseUrlFromEnv(): string {
  return process.env.BASE_URL || "https://quefairedemesdechets.ademe.fr"
}
