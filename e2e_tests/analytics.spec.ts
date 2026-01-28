import { test, expect } from "@playwright/test"
import { navigateTo, TIMEOUT } from "./helpers"

test.describe("📊 Analytics & Tracking", () => {
  test.describe("Tracking du referrer dans les iframes", () => {
    test("Le referrer complet avec query string est encodé dans le paramètre ref de l'iframe", async ({
      page,
    }) => {
      // Navigate to the test page with query parameters to test full URL capture
      const testQueryParams = "test_param=value&another=123"
      const fullPageUrl = `/lookbook/preview/tests/t_1_referrer?script_type=carte&${testQueryParams}`
      await navigateTo(page, fullPageUrl)

      // Get the parent window location for comparison (should include query params)
      const parentLocation = page.url()
      expect(parentLocation).toContain(testQueryParams)

      // Wait for the carte iframe to be created
      const iframeLocator = page.locator("iframe#carte")
      await expect(iframeLocator).toBeAttached({ timeout: TIMEOUT.DEFAULT })

      // Get the iframe src attribute
      const iframeSrc = await iframeLocator.getAttribute("src")
      expect(iframeSrc).not.toBeNull()
      expect(iframeSrc).toContain("ref=")

      // Extract and decode the ref parameter
      const url = new URL(iframeSrc!, "http://localhost")
      const refParam = url.searchParams.get("ref")
      expect(refParam).not.toBeNull()

      // Decode base64 ref parameter
      const decodedRef = Buffer.from(refParam!, "base64").toString("utf-8")

      // Verify the decoded referrer matches the parent URL with query params
      expect(decodedRef).toContain(testQueryParams)
      expect(decodedRef).toContain("/lookbook/preview/tests/t_1_referrer")
    })
  })
})
