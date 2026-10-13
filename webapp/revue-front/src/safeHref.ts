/**
 * Keeps a same-origin path (`/…`) and replaces anything else with `/`.
 *
 * General URL sanitizers (for example `@braintree/sanitize-url`) still allow
 * absolute `http(s):` URLs and treat a leading `/` as relative, so `//host`
 * passes through. This allowlist is the check those packages do not provide.
 * A backslash is rejected as well: browsers normalize `/\host` to `//host`.
 */
export function toSafeInternalHref(value: string): string {
  const trimmed = value.trim()
  if (!trimmed.startsWith("/") || trimmed.startsWith("//") || trimmed.includes("\\")) {
    return "/"
  }
  if (/^[a-zA-Z][a-zA-Z\d+\-.]*:/.test(trimmed)) {
    return "/"
  }
  return trimmed
}
