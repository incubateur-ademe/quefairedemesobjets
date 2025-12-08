/**
 * Tests for url_utils module
 */

import { getBaseUrlFromScript } from "../js/url_utils"

// Mock process.env
const originalEnv = process.env
beforeEach(() => {
  jest.resetModules()
  process.env = { ...originalEnv }
})

afterEach(() => {
  process.env = originalEnv
})

describe("getBaseUrlFromScript", () => {
  describe("with absolute HTTPS URLs", () => {
    it("should extract origin from absolute https URL", () => {
      const script = document.createElement("script")
      script.setAttribute("src", "https://example.com/path/to/script.js")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://example.com")
    })

    it("should extract origin from absolute http URL", () => {
      const script = document.createElement("script")
      script.setAttribute("src", "http://example.com/path/to/script.js")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("http://example.com")
    })

    it("should handle URLs with ports", () => {
      const script = document.createElement("script")
      script.setAttribute("src", "https://example.com:8080/script.js")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://example.com:8080")
    })
  })

  describe("with protocol-relative URLs", () => {
    it("should convert protocol-relative URL to https", () => {
      const script = document.createElement("script")
      script.setAttribute("src", "//example.com/path/to/script.js")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://example.com")
    })

    it("should handle protocol-relative URLs with ports", () => {
      const script = document.createElement("script")
      script.setAttribute("src", "//example.com:3000/script.js")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://example.com:3000")
    })

    it("should handle protocol-relative URLs with subdomains", () => {
      const script = document.createElement("script")
      script.setAttribute("src", "//subdomain.example.com/script.js")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://subdomain.example.com")
    })
  })

  describe("with ALLOWED_HOSTS validation", () => {
    it("should allow exact hostname match", () => {
      process.env.ALLOWED_HOSTS = "example.com,test.com"
      const script = document.createElement("script")
      script.setAttribute("src", "https://example.com/script.js")

      // Need to re-import to pick up new env vars
      jest.isolateModules(() => {
        const { getBaseUrlFromScript } = require("../js/url_utils")
        const result = getBaseUrlFromScript(script)
        expect(result).toBe("https://example.com")
      })
    })

    it("should allow wildcard (*) to accept any host", () => {
      process.env.ALLOWED_HOSTS = "*"
      const script = document.createElement("script")
      script.setAttribute("src", "https://anything.com/script.js")

      jest.isolateModules(() => {
        const { getBaseUrlFromScript } = require("../js/url_utils")
        const result = getBaseUrlFromScript(script)
        expect(result).toBe("https://anything.com")
      })
    })

    it("should fall back to BASE_URL for disallowed host", () => {
      process.env.ALLOWED_HOSTS = "example.com"
      process.env.BASE_URL = "https://fallback.com"
      const script = document.createElement("script")
      script.setAttribute("src", "https://malicious.com/script.js")

      jest.isolateModules(() => {
        const { getBaseUrlFromScript } = require("../js/url_utils")
        const result = getBaseUrlFromScript(script)
        expect(result).toBe("https://fallback.com")
      })
    })
  })

  describe("error handling", () => {
    it("should fall back to BASE_URL when script tag is null", () => {
      process.env.BASE_URL = "https://fallback.com"

      const result = getBaseUrlFromScript(null)

      expect(result).toBe("https://fallback.com")
    })

    it("should fall back to BASE_URL when src attribute is missing", () => {
      process.env.BASE_URL = "https://fallback.com"
      const script = document.createElement("script")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://fallback.com")
    })

    it("should fall back to BASE_URL when src is invalid", () => {
      process.env.BASE_URL = "https://fallback.com"
      const script = document.createElement("script")
      script.setAttribute("src", "not-a-valid-url")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://fallback.com")
    })

    it("should return empty string when BASE_URL is not set and parsing fails", () => {
      delete process.env.BASE_URL
      const script = document.createElement("script")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("")
    })
  })

  describe("real-world scenarios", () => {
    it("should handle Django Lookbook preview with protocol-relative URL", () => {
      process.env.BASE_URL = "https://quefairedemesdechets.ademe.local"
      const script = document.createElement("script")
      script.setAttribute("src", "//quefairedemesdechets.ademe.local/infotri/iframe.js")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://quefairedemesdechets.ademe.local")
    })

    it("should handle production embed with absolute URL", () => {
      const script = document.createElement("script")
      script.setAttribute("src", "https://quefairedemesobjets.ademe.fr/static/carte.js")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://quefairedemesobjets.ademe.fr")
    })

    it("should handle local development URL", () => {
      const script = document.createElement("script")
      script.setAttribute("src", "https://quefairedemesdechets.ademe.local/iframe.js")

      const result = getBaseUrlFromScript(script)

      expect(result).toBe("https://quefairedemesdechets.ademe.local")
    })
  })
})
