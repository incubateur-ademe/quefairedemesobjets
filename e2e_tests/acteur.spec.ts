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
