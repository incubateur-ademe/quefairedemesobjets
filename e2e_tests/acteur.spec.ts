import { test, expect } from "@playwright/test"
import {
  navigateTo,
  getIframe,
  mockApiAdresse,
  searchAddress,
  TIMEOUT,
} from "./helpers"

test.describe("📋 Fiche Acteur Viewport", () => {
  test(
    "La fiche acteur est visible dans le viewport sans scroll sur mobile",
    { tag: ["@mobile"] },
    async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/tests/t_15_acteur_fiche_viewport")

      const iframe = getIframe(page, "assistant")
      await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

      // Scroll the search form into view
      const searchForm = iframe
        .locator('[data-controller="search-solution-form"]')
        .first()
      await searchForm.scrollIntoViewIfNeeded()

      // Wait for the carte turbo-frame to load inside the produit page
      await mockApiAdresse(page)
      const mauvaisEtatPanel = iframe.locator("#mauvais-etat-panel")
      await expect(mauvaisEtatPanel).toBeAttached({ timeout: TIMEOUT.DEFAULT })
      await expect(
        mauvaisEtatPanel.locator('[data-testid="carte-adresse-input"]'),
      ).toBeVisible({ timeout: TIMEOUT.DEFAULT })

      // Search for Auray in the carte embedded in the produit page
      await searchAddress(iframe, "Auray", "carte", {
        parentLocator: mauvaisEtatPanel,
      })

      // Wait for acteur markers to appear
      const acteurMarkers = iframe.locator(
        '.maplibregl-marker[data-controller="pinpoint"]:not(#pinpoint-home)',
      )
      await expect(acteurMarkers.first()).toBeVisible({ timeout: TIMEOUT.LONG })

      // Click on the first acteur marker via evaluate to trigger proper navigation
      await acteurMarkers.first().evaluate((el: HTMLElement) => el.click())

      // Wait for the acteur detail panel in the mauvais-etat tab to be shown
      const acteurDetailsPanel = mauvaisEtatPanel.locator("#acteurDetailsPanel")
      await expect(acteurDetailsPanel).toHaveAttribute("aria-hidden", "false", {
        timeout: TIMEOUT.DEFAULT,
      })

      // Assert that the acteur title is visible in the viewport without scrolling
      const acteurTitle = iframe.getByTestId("acteur-title")
      await expect(acteurTitle).toBeVisible({ timeout: TIMEOUT.DEFAULT })
      await expect(acteurTitle).toBeInViewport()
    },
  )
})

test.describe("📤 Acteur Share", () => {
  test.beforeEach(async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(["clipboard-read", "clipboard-write"])

    // Navigate directly to the acteur preview page
    await page.goto("/lookbook/preview/pages/acteur", {
      waitUntil: "domcontentloaded",
    })
  })

  // This test is skipped because the tooltip on http://quefairedemesdechets.ademe.local/lookbook/preview/pages/acteur/
  // cannot be properly displayed on hover.
  // The position of the tooltip continuously change, which is not an intended behaviour.
  // To be adresses when we will remove the tooltip, that is not accessible.
  test.skip("Le bouton copier dans le presse-papier copie l'URL complète de l'acteur", async ({
    page,
  }) => {
    // Click the share button to open the tooltip (using aria-describedby to find it)
    const shareButton = page.getByRole("button", { name: "partager" })
    await shareButton.click()

    // Wait for the tooltip to be visible (using role="tooltip")
    await page.waitForSelector('[role="tooltip"]', { state: "visible" })

    // Get the URL from the copy button's span before clicking (using stimulus data attribute)
    const urlInButton = await page.locator('[data-copy-target="toCopy"]').textContent()

    expect(urlInButton).toBeTruthy()
    expect(urlInButton).toMatch(/^https?:\/\//) // Should be a full URL with protocol

    // Click the copy button using JavaScript since the tooltip is positioned outside viewport
    // Use stimulus data-action attribute to find the button
    await page.evaluate(() => {
      const btn = document.querySelector('[data-action="copy#toClipboard"]')
      btn?.click()
    })

    // Verify clipboard content matches the URL in the button
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipboardText).toBe(urlInButton)
    expect(clipboardText).toContain("/adresse_details/") // Should contain the acteur path
  })
})
