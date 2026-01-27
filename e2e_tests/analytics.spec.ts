import { test, expect } from "@playwright/test"
import { navigateTo, getIframe, TIMEOUT } from "./helpers"

test.describe("📊 Analytics & Tracking", () => {
  test.describe("Tracking du referrer dans les iframes", () => {
    test("Le referrer parent est correctement tracké lors des clics sur des liens dans l'iframe", async ({
      page,
    }) => {
      // Navigate to the test page with query parameters to test full URL capture
      // Uses script_type=assistant to load the assistant template (has clickable links)
      const testQueryParams = "test_param=value&another=123"
      const fullPageWithQueryParams = `/lookbook/preview/tests/t_1_referrer?script_type=assistant&${testQueryParams}`
      await navigateTo(page, fullPageWithQueryParams)

      // Get the parent window location for comparison (should include query params)
      const parentLocation = page.url()
      expect(parentLocation).toContain(testQueryParams)

      // Locate the assistant iframe
      const iframe = getIframe(page, "assistant")

      // Wait for iframe to load by waiting for the body with Stimulus controller
      await expect(iframe.locator("body[data-controller*='analytics']")).toBeAttached({
        timeout: TIMEOUT.DEFAULT,
      })

      // Find a visible link using Playwright's built-in visibility detection
      const visibleLink = iframe.locator("a:visible").first()
      await expect(visibleLink).toBeVisible({ timeout: TIMEOUT.DEFAULT })

      // Get the current URL before clicking to detect navigation
      const initialUrl = await iframe
        .locator("body")
        .evaluate(() => window.location.href)

      await visibleLink.click()

      // Wait for navigation by checking that the URL has actually changed
      await expect(async () => {
        const currentUrl = await iframe
          .locator("body")
          .evaluate(() => window.location.href)
        expect(currentUrl).not.toBe(initialUrl)
      }).toPass({ timeout: TIMEOUT.DEFAULT })

      // Wait for the analytics controller to be available after navigation
      await expect(async () => {
        const hasController = await iframe.locator("body").evaluate(() => {
          return !!(window as any).stimulus?.getControllerForElementAndIdentifier(
            document.querySelector("body"),
            "analytics",
          )
        })
        expect(hasController).toBe(true)
      }).toPass({ timeout: TIMEOUT.SHORT })

      // Execute JavaScript inside the iframe to get personProperties
      // This can seem a bit cumbersome, but is the result of quite a lot of trial
      // and error.
      // Playwright does not play well with iframes...
      const personProperties = await iframe.locator("body").evaluate(() => {
        const controller = (
          window as any
        ).stimulus?.getControllerForElementAndIdentifier(
          document.querySelector("body"),
          "analytics",
        )
        if (!controller) {
          return null
        }
        return controller.personProperties
      })

      // Verify analytics controller is loaded
      expect(personProperties).not.toBeNull()

      // Verify that iframe is set to true
      expect(personProperties.iframe).toBe(true)

      // Verify that iframeReferrer is set and matches the parent window location
      expect(personProperties.iframeReferrer).toBeDefined()
      expect(personProperties.iframeReferrer).toBe(parentLocation)
    })
  })
})
