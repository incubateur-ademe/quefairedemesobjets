import { test, expect } from "@playwright/test"
import { navigateTo, TIMEOUT } from "./helpers"

test.describe("Navigation dans le header", () => {
  test("Test link on logo", async ({ page }) => {
    await navigateTo(page, "/")

    // Navigate to a sub-page by clicking a category link in the main content.
    // The homepage's category cards link to /categories/<slug>/.
    const pageLink = page.locator("a[href^='/categories/']").first()
    await pageLink.waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })
    await pageLink.click()
    await page.waitForURL(/\/categories\//, { timeout: TIMEOUT.DEFAULT })
    const subPageUrl = page.url()

    // Click on logo parent → should go back to home
    await page.locator(".fr-header__operator").click()
    expect(page.url()).not.toBe(subPageUrl)
  })
})
