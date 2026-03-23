import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

test.describe("Navigation dans le header", () => {
  test("Test link on logo", async ({ page }) => {
    await navigateTo(page, "/")

    // Click on the second link in the navbar
    await page.locator("#fr-navigation .fr-nav__item:nth-of-type(2) a").click()
    await page.locator("#fr-navigation .fr-nav__item:nth-of-type(2) a").click()
    await expect(
      page.locator("#fr-navigation .fr-nav__item:nth-of-type(2) a"),
    ).toHaveAttribute("aria-current", "true")
    const previousUrl = page.url()

    // Click on logo parent
    await page.locator(".fr-header__operator").click()
    expect(page.url()).not.toBe(previousUrl)
  })
})
