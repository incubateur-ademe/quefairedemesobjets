import { AxeBuilder } from "@axe-core/playwright"
import { test, expect } from "@playwright/test"

test.describe("♿ Conformité Accessibilité WCAG", () => {
  // Shared variables
  const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
  const IFRAME_SELECTOR = "iframe"

  test.describe("Conformité WCAG 2.1 AA des pages principales", () => {
    test("L'iframe du formulaire respecte les critères WCAG 2.1 AA", async ({
      page,
    }) => {
      await page.goto(`/lookbook/preview/iframe/formulaire/`, {
        waitUntil: "domcontentloaded",
      })

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include(IFRAME_SELECTOR) // Restrict scan to the iframe
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })

    test("L'iframe de la carte respecte les critères WCAG 2.1 AA", async ({ page }) => {
      await page.goto(`/lookbook/preview/iframe/carte/`, {
        waitUntil: "domcontentloaded",
      })

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include(IFRAME_SELECTOR) // Restrict scan to the iframe
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })

    test("La page d'accueil de l'assistant respecte les critères WCAG 2.1 AA", async ({
      page,
    }) => {
      // TODO: Update the route for production
      await page.goto(`/`, { waitUntil: "domcontentloaded" })

      const accessibilityScanResults = await new AxeBuilder({ page })
        .exclude("[data-disable-axe]")
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })

    test("La page de détail produit de l'assistant respecte les critères WCAG 2.1 AA", async ({
      page,
    }) => {
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
})
