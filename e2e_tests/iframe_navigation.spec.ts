import { test, expect } from "@playwright/test"
import { navigateTo, getIframe, TIMEOUT } from "./helpers"

test.describe("🧭 Navigation dans l'iframe avec persistance de l'UI", () => {
  test("L'interface iframe persiste lors de la navigation", async ({ page }) => {
    // Navigate to the test preview page
    await navigateTo(page, "/lookbook/preview/tests/t_8_iframe_navigation_persistence")

    // Wait for iframe to be created by the integration script (uses first iframe, no specific id)
    const iframe = getIframe(page)
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    // Helper function to check iframe-specific UI elements
    const checkIframeUI = async () => {
      // Check that header is NOT present (hidden in iframe mode)
      await expect(iframe.locator(".fr-header")).not.toBeVisible()

      // Check that footer is NOT present (hidden in iframe mode)
      await expect(iframe.locator(".fr-footer")).not.toBeVisible()

      // Check that iframe-specific link is present
      await expect(
        iframe.locator('a:has-text("En savoir plus sur ce site")'),
      ).toBeVisible()
    }

    // Initial page load - verify iframe UI
    await checkIframeUI()

    // Navigate to a product page by using the search functionality
    // The carousel links are hidden, so we use the search input instead
    const searchInput = iframe.locator('input[data-search-target="input"]')
    await expect(searchInput).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    await searchInput.click()
    // Type search term and wait for results to appear
    await searchInput.pressSequentially("chaussures", { delay: 50 })

    // Wait for search results to appear in the turbo frame
    const autocompleteResult = iframe.getByRole("link", {
      name: "Chaussures",
      exact: true,
    })
    // Use retry logic: if autocomplete doesn't appear, try pressing a key to trigger it
    try {
      await expect(autocompleteResult).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    } catch {
      // Retry by pressing space then backspace to trigger search
      await searchInput.press("Space")
      await searchInput.press("Backspace")
      await expect(autocompleteResult).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    }
    await autocompleteResult.click()

    // Wait for product page to load (heading with product name)
    await iframe.locator("h1").waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })

    // Verify iframe UI persists on product page
    await checkIframeUI()
  })

  test("Les liens internes maintiennent le mode iframe", async ({ page }) => {
    // Navigate to the test preview page
    await navigateTo(page, "/lookbook/preview/tests/t_8_iframe_navigation_persistence")

    // Wait for iframe to be created (uses first iframe, no specific id)
    const iframe = getIframe(page)
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    // Navigate to a product page using the search
    const searchInput = iframe.locator('input[data-search-target="input"]')
    await expect(searchInput).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    await searchInput.click()
    await searchInput.pressSequentially("ecran", { delay: 50 })

    const autocompleteResult = iframe.getByRole("link", {
      name: "Écran",
      exact: true,
    })
    try {
      await expect(autocompleteResult).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    } catch {
      await searchInput.press("Space")
      await searchInput.press("Backspace")
      await expect(autocompleteResult).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    }
    await autocompleteResult.click()

    // Wait for product page to load
    await iframe.locator("h1").waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })
    await expect(iframe.locator("h1")).toContainText("Écran", {
      timeout: TIMEOUT.DEFAULT,
    })

    // Verify iframe-specific UI is still present after navigation
    // The iframe has its own minimal header (data-testid="header-iframe") which is fine
    // We check that the full site header (without header-iframe testid) is NOT visible
    await expect(
      iframe.locator('.fr-header:not([data-testid="header-iframe"])'),
    ).not.toBeVisible()
    await expect(
      iframe.locator('a:has-text("En savoir plus sur ce site")'),
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
  })
})
