import { test, expect, FrameLocator } from "@playwright/test"
import { navigateTo, getIframe, TIMEOUT } from "./helpers"
import { typeSearchQuery, waitForResults } from "./search.spec"

// Helper function to check iframe-specific UI elements
const checkIframeUIIsPersisted = async (iframe: FrameLocator) => {
  // Verify iframe-specific UI is still present after navigation
  // The iframe has its own minimal header (data-testid="header-iframe") which is fine
  // We check that the full site header (without header-iframe testid) is NOT visible
  await expect(
    iframe.locator('.fr-header:not([data-testid="header-iframe"])'),
  ).not.toBeVisible()
  await expect(
    iframe.locator('button:has-text("En savoir plus sur ce site")'),
  ).toBeVisible()

  // Check that iframe-specific button is present
  await expect(
    iframe.locator('button:has-text("En savoir plus sur ce site")'),
  ).toBeVisible()

  // Navigate using an external link on the product page to test internal navigation
  // Click on one of the "En savoir plus" links which are internal links
  const externalInfoLink = iframe.locator('a[href*="refashion.fr"]').first()
  if (await externalInfoLink.isVisible()) {
    // External links should open in new tab - verify they have correct attributes
    const target = await externalInfoLink.getAttribute("target")
    expect(target).toBe("_blank")
  }

  // Verify footer is still not visible (part of iframe mode)
  await expect(iframe.locator(".fr-footer")).not.toBeVisible()
}

test.describe("🧭 Navigation dans l'iframe avec persistance de l'UI", () => {
  test("L'interface iframe persiste lors de la navigation", async ({ page }) => {
    // Navigate to the test preview page
    await navigateTo(page, "/lookbook/preview/tests/t_8_iframe_navigation_persistence")

    // Wait for iframe to be created by the integration script (uses first iframe, no specific id)
    const iframe = getIframe(page)
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    // Initial page load - verify iframe UI
    await checkIframeUIIsPersisted(iframe)

    // Navigate to a product page by using the search functionality
    // The carousel links are hidden, so we use the search input instead
    await typeSearchQuery(iframe, "écran")
    const results = await waitForResults(iframe)
    results.first().click()

    // Wait for product page to load (heading with product name)
    await iframe.locator("h1").waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })
    await expect(iframe.locator("h1")).toContainText("Écran", {
      timeout: TIMEOUT.DEFAULT,
    })

    // Verify iframe UI persists on product page
    await checkIframeUIIsPersisted(iframe)
  })

  test("Les liens internes maintiennent le mode iframe", async ({ page }) => {
    // Navigate to the test preview page
    await navigateTo(page, "/lookbook/preview/tests/t_8_iframe_navigation_persistence")

    // Wait for iframe to be created (uses first iframe, no specific id)
    const iframe = getIframe(page)
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    await typeSearchQuery(iframe, "écran")
    const results = await waitForResults(iframe)
    results.first().click()

    // Wait for product page to load
    await iframe.locator("h1").waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })
    await expect(iframe.locator("h1")).toContainText("Écran", {
      timeout: TIMEOUT.DEFAULT,
    })

    await checkIframeUIIsPersisted(iframe)
  })
})
