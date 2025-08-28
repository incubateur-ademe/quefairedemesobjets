import { AxeBuilder } from "@axe-core/playwright"
import { expect } from "@playwright/test"
import { test } from "./config"

// Shared variables
const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
const IFRAME_SELECTOR = "iframe"

test.describe("WCAG Compliance Tests", () => {
  test("Formulaire iFrame", async ({ page }) => {
    await page.goto(`/test_iframe`, { waitUntil: "domcontentloaded" })

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include(IFRAME_SELECTOR) // Restrict scan to the iframe
      .withTags(WCAG_TAGS)
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test("Carte iFrame", async ({ page }) => {
    await page.goto(`/test_iframe?test_carte`, { waitUntil: "domcontentloaded" })

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include(IFRAME_SELECTOR) // Restrict scan to the iframe
      .withTags(WCAG_TAGS)
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test("Assistant Homepage", async ({ page }) => {
    // TODO: Update the route for production
    await page.goto(`/`, { waitUntil: "domcontentloaded" })

    const accessibilityScanResults = await new AxeBuilder({ page })
      .exclude("[data-disable-axe]")
      .withTags(WCAG_TAGS)
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test("Assistant Detail Page", async ({ page }) => {
    await page.goto(`/dechet/smartphone`, {
      waitUntil: "domcontentloaded",
    })

    const accessibilityScanResults = await new AxeBuilder({ page })
      .exclude("[data-disable-axe]")
      // ImpactCO2 iframe does not load during e2e tests, it is safe
      // to exclude it usually includes a title and is a valid <iframe>
      // tag.
      .exclude('iframe[src*="impactco2.fr"]')
      .withTags(WCAG_TAGS)
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })
})
