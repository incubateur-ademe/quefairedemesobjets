import { test, expect } from "@playwright/test"

test.describe("📤 Acteur Share", () => {
  test.beforeEach(async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(["clipboard-read", "clipboard-write"])

    // Navigate directly to the acteur preview page
    await page.goto("/lookbook/preview/pages/acteur", {
      waitUntil: "domcontentloaded",
    })
  })

  test("Le bouton copier dans le presse-papier copie l'URL complète de l'acteur", async ({
    page,
  }) => {
    // Click the share button to open the tooltip
    const shareButton = page.locator("button.fr-icon-share-line")
    await shareButton.click()

    // Wait for the tooltip to be visible
    await page.waitForSelector(".fr-tooltip", { state: "visible" })

    // Get the URL from the copy button's span before clicking
    const urlInButton = await page
      .locator('.fr-btn--copy [data-copy-target="toCopy"]')
      .textContent()

    expect(urlInButton).toBeTruthy()
    expect(urlInButton).toMatch(/^https?:\/\//) // Should be a full URL with protocol

    // Click the copy button using JavaScript since the tooltip is positioned outside viewport
    await page.evaluate(() => {
      const btn = document.querySelector(".fr-btn--copy")
      btn?.click()
    })

    // Verify clipboard content matches the URL in the button
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipboardText).toBe(urlInButton)
    expect(clipboardText).toContain("/adresse_details/") // Should contain the acteur path
  })
})
