import { test, expect } from "@playwright/test"

test.describe("📋 Test de la fonctionnalité de copie au clic", () => {
  test.beforeEach(async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(["clipboard-read", "clipboard-write"])
    await page.goto("/lookbook/preview/tests/t_7_copy_controller", {
      waitUntil: "domcontentloaded",
    })
  })

  test("Le bouton change de texte après copie", async ({ page }) => {
    const copyButton = page.locator('[data-testid="copy-button"]')

    // Verify initial button text
    await expect(copyButton).toContainText("Copier")

    // Click the copy button
    await copyButton.click()

    // Verify button text changed
    await expect(copyButton).toContainText("Copié !")

    // Verify clipboard content
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipboardText).toBe("Texte à copier pour le test")
  })

  test("La copie fonctionne sans bouton target", async ({ page }) => {
    const copyButton = page.locator('[data-testid="copy-url-button"]')
    const textToCopy = page.locator('[data-testid="url-to-copy"]')

    // Get the text that should be copied
    const expectedText = await textToCopy.textContent()

    // Click the copy button
    await copyButton.click()

    // Verify clipboard content
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipboardText).toBe(expectedText)

    // Button text should not change (no data-copy-copied-value)
    await expect(copyButton).toContainText("📋 Copier l'URL")
  })

  test("La copie depuis un span inline fonctionne", async ({ page }) => {
    const copyButton = page.locator('[data-testid="copy-inline-button"]')
    const textToCopy = page
      .locator('[data-testid="copy-inline"]')
      .locator('[data-copy-target="toCopy"]')

    // Get the text that should be copied
    const expectedText = await textToCopy.textContent()

    // Click the copy button
    await copyButton.click()

    // Verify clipboard content
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipboardText).toBe(expectedText)
  })

  test("Les multiples contrôleurs copy fonctionnent indépendamment", async ({
    page,
  }) => {
    const firstButton = page.locator('[data-testid="copy-button"]')
    const secondButton = page.locator('[data-testid="copy-url-button"]')

    // Click first button
    await firstButton.click()
    let clipboardText = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipboardText).toBe("Texte à copier pour le test")
    await expect(firstButton).toContainText("Copié !")

    // Click second button
    await secondButton.click()
    clipboardText = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipboardText).toBe("https://example.com/test-url")

    // First button should still show "Copié !" (it doesn't reset)
    await expect(firstButton).toContainText("Copié !")
    // Second button should not change (no data-copy-copied-value)
    await expect(secondButton).toContainText("📋 Copier l'URL")
  })
})
