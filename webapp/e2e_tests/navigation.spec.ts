import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

test.describe("Navigation dans le header", () => {
  test("Test link on logo", async ({ page }) => {
    await navigateTo(page, "/")

    // Navigate to a sub-page by clicking a page link in the main content
    // The homepage has links like "Petit électroménager", "Déchets alimentaires", etc.
    await page.locator("a[href^='/produit/'], a[href^='/dechet/']").first().click()
    await page.waitForURL(/\/produit\/|\/dechet\//)
    const subPageUrl = page.url()

    // Click on logo parent → should go back to home
    await page.locator(".fr-header__operator").click()
    expect(page.url()).not.toBe(subPageUrl)
  })
})
