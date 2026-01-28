import { test, expect } from "@playwright/test"
import { navigateTo, TIMEOUT } from "./helpers"

test.describe("📊 Analytics & Tracking", () => {
  test.describe("Tracking du referrer dans les iframes", () => {
    const scriptTypes = [
      { name: "carte", scriptType: "carte", iframeId: "carte", iframePath: "/carte" },
      {
        name: "assistant",
        scriptType: "assistant",
        iframeId: "assistant",
        iframePath: "/dechet",
      },
    ]

    for (const { name, scriptType, iframeId, iframePath } of scriptTypes) {
      test(`Le referrer parent avec query string est correctement passé à l'iframe pour ${name}`, async ({
        page,
      }) => {
        // Navigate to the test page with the script_type parameter and additional query params
        // The script_type selects which template to render via django-lookbook form
        const testQueryParams = "test_param=value&another=123"
        const fullUrl = `/lookbook/preview/tests/t_1_referrer?script_type=${scriptType}&${testQueryParams}`
        await navigateTo(page, fullUrl)

        // Get the parent window location for comparison (must include query params)
        const parentLocation = page.url()
        expect(parentLocation).toContain(testQueryParams)

        // Wait for the iframe to be created with the correct ID
        const iframeLocator = page.locator(`iframe#${iframeId}`)
        await expect(iframeLocator).toBeAttached({ timeout: TIMEOUT.DEFAULT })

        // Get the iframe src attribute and verify it contains the ref parameter
        const iframeSrc = await iframeLocator.getAttribute("src")
        expect(iframeSrc).not.toBeNull()
        expect(iframeSrc).toContain(iframePath)
        expect(iframeSrc).toContain("ref=")

        // Decode the ref parameter and verify it matches the parent URL
        const url = new URL(iframeSrc!, "http://localhost")
        const refParam = url.searchParams.get("ref")
        expect(refParam).not.toBeNull()

        // Decode base64 ref parameter
        const decodedRef = Buffer.from(refParam!, "base64").toString("utf-8")

        // Verify the decoded referrer contains the test query params
        expect(decodedRef).toContain(testQueryParams)
      })
    }
  })
})
