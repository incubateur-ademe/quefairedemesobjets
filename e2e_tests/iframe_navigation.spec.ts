import { test, expect } from "@playwright/test"
import { navigateTo, getIframe, TIMEOUT } from "./helpers"

test.describe("🧭 Navigation dans l'iframe avec persistance de l'UI", () => {
  test("L'interface iframe persiste lors de la navigation", async ({ page }) => {
    // Navigate to the test preview page
    await navigateTo(page, "/lookbook/preview/tests/t_6_iframe_navigation_persistence")

    // Wait for iframe to be created by the integration script
    const iframe = getIframe(page, "assistant")
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    // Helper function to check iframe-specific UI elements
    const checkIframeUI = async () => {
      // Check that header is NOT present (hidden in iframe mode)
      await expect(iframe.locator(".fr-header")).not.toBeVisible()

      // Check that footer is NOT present (hidden in iframe mode)
      await expect(iframe.locator(".fr-footer")).not.toBeVisible()

      // Check that iframe footer links ARE present
      await expect(
        iframe.locator("text=Réutiliser cette carte sur mon site"),
      ).toBeVisible()
      await expect(iframe.locator("text=Participer à son amélioration")).toBeVisible()
    }

    // Initial page load - verify iframe UI
    await checkIframeUI()

    // Navigate to a product page by clicking search
    const searchInput = iframe.locator('input[name="header-q"]')
    await searchInput.fill("vélo")
    await searchInput.press("Enter")

    // Wait for navigation to complete
    await iframe
      .locator("text=/vélo/i")
      .first()
      .waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })

    // Verify iframe UI persists after search
    await checkIframeUI()

    // Click on a search result
    const firstResult = iframe.locator('[data-testid="suggestion-item"]').first()
    if (await firstResult.isVisible()) {
      await firstResult.click()

      // Wait for product page to load
      await iframe
        .locator("text=/que faire/i")
        .waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })

      // Verify iframe UI persists on product page
      await checkIframeUI()
    }

    // Navigate back using browser back button if available
    const backButton = iframe.locator("text=/retour/i").first()
    if (await backButton.isVisible()) {
      await backButton.click()

      // Wait for previous page to load
      await iframe
        .locator("body")
        .waitFor({ state: "attached", timeout: TIMEOUT.DEFAULT })

      // Verify iframe UI still persists
      await checkIframeUI()
    }
  })

  test("Les liens internes maintiennent le mode iframe", async ({ page }) => {
    // Navigate to the test preview page
    await navigateTo(page, "/lookbook/preview/tests/t_6_iframe_navigation_persistence")

    // Wait for iframe to be created
    const iframe = getIframe(page, "assistant")
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    // Find an internal link in the iframe (if any exist)
    const internalLinks = iframe.locator('a[href^="/"]')
    const linkCount = await internalLinks.count()

    if (linkCount > 0) {
      // Get the first internal link
      const firstLink = internalLinks.first()
      await firstLink.click()

      // Wait for navigation
      await iframe
        .locator("body")
        .waitFor({ state: "attached", timeout: TIMEOUT.DEFAULT })

      // Verify iframe-specific UI is still present
      await expect(iframe.locator(".fr-header")).not.toBeVisible()
      await expect(
        iframe.locator("text=Réutiliser cette carte sur mon site"),
      ).toBeVisible()
    }
  })
})
