/**
 * Keeps a same-origin path (`/…`) and replaces anything else with `/`.
 *
 * General URL sanitizers (for example `@braintree/sanitize-url`) still allow
 * absolute `http(s):` URLs and treat a leading `/` as relative, so `//host`
 * passes through. This allowlist is the check those packages do not provide.
 * The value is resolved by the URL parser rather than matched as a string:
 * browsers normalize `/\host` to `//host` and strip tabs and newlines anywhere
 * in a URL, so `/\t/host` also points to another origin.
 */
export function toSafeInternalHref(value: string): string {
  const trimmed = value.trim()
  if (!trimmed.startsWith("/")) {
    return "/"
  }
  let url: URL
  try {
    url = new URL(trimmed, window.location.origin)
  } catch {
    return "/"
  }
  if (url.origin !== window.location.origin) {
    return "/"
  }
  // The URL parser leaves `'` in the path and the fragment. Percent-encode the
  // HTML meta-characters so this string cannot be reinterpreted as markup.
  return `${url.pathname}${url.search}${url.hash}`.replace(/[<>"']/g, (character) => {
    switch (character) {
      case "<":
        return "%3C"
      case ">":
        return "%3E"
      case '"':
        return "%22"
      default:
        return "%27"
    }
  })
}
