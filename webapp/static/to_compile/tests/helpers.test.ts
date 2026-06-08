import { clearSearchTermCookie, setSearchTermCookie } from "../js/helpers"

describe("search term cookie helpers", () => {
  let written: string

  beforeEach(() => {
    written = ""
    // jsdom returns "" for document.cookie by default. Intercept assignments
    // so we can inspect the raw cookie string, attributes included (jsdom's
    // document.cookie getter strips attributes).
    Object.defineProperty(document, "cookie", {
      configurable: true,
      get: () => written,
      set: (value: string) => {
        written = value
      },
    })
  })

  describe("setSearchTermCookie", () => {
    it("writes the cookie name and value", () => {
      setSearchTermCookie("42")

      expect(written).toContain("qf_search_term_id=42")
    })

    it("accepts a numeric id", () => {
      setSearchTermCookie(7)

      expect(written).toContain("qf_search_term_id=7")
    })

    it("uses attributes that allow cross-site iframe reads", () => {
      // SameSite=None lets the cookie be sent on iframe navigations from a
      // different top-level site. Secure is mandatory when SameSite=None.
      // Partitioned (CHIPS) keeps the cookie scoped to the embedding site so
      // it cannot be used for cross-site tracking.
      setSearchTermCookie("42")

      expect(written).toContain("SameSite=None")
      expect(written).toContain("Secure")
      expect(written).toContain("Partitioned")
      expect(written).not.toContain("SameSite=Lax")
    })

    it("scopes the cookie to the whole site with a short lifetime", () => {
      setSearchTermCookie("42")

      expect(written).toContain("path=/")
      expect(written).toContain("max-age=10")
    })
  })

  describe("clearSearchTermCookie", () => {
    it("expires the cookie immediately", () => {
      clearSearchTermCookie()

      expect(written).toContain("qf_search_term_id=")
      expect(written).toContain("max-age=0")
    })

    it("matches the attributes used when writing so the browser overwrites the cookie", () => {
      // Some browsers refuse to overwrite a Partitioned cookie with a
      // non-Partitioned one, leaving the original value stale. The clear
      // attributes must mirror the set attributes.
      clearSearchTermCookie()

      expect(written).toContain("path=/")
      expect(written).toContain("SameSite=None")
      expect(written).toContain("Secure")
      expect(written).toContain("Partitioned")
    })
  })
})
