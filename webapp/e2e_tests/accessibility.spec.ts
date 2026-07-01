import { AxeBuilder } from "@axe-core/playwright"
import { test, expect } from "@playwright/test"
import {
  clickFirstClickableActeurMarker,
  mockApiAdresse,
  navigateTo,
  searchCarteAndWaitForActeurs,
  switchToListeMode,
} from "./helpers"

test.describe("♿ Conformité Accessibilité WCAG", () => {
  // Shared variables
  const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
  const IFRAME_SELECTOR = "iframe"

  test.describe("Conformité WCAG 2.1 AA des pages principales", () => {
    test("L'iframe du formulaire respecte les critères WCAG 2.1 AA", async ({
      page,
    }) => {
      await navigateTo(page, `/lookbook/preview/iframe/formulaire/`)

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include(IFRAME_SELECTOR) // Restrict scan to the iframe
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })

    test("L'iframe de la carte respecte les critères WCAG 2.1 AA", async ({ page }) => {
      await navigateTo(page, `/lookbook/preview/iframe/carte/`)

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
      await navigateTo(page, `/`)

      const accessibilityScanResults = await new AxeBuilder({ page })
        .exclude("[data-disable-axe]")
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })

    test("La page de détail produit de l'assistant respecte les critères WCAG 2.1 AA", async ({
      page,
    }) => {
      await navigateTo(page, `/dechet/smartphone`)

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

  test.describe("Conformité WCAG 2.1 AA après interactions", () => {
    test("La carte avec résultats et acteur detail ouvert respecte WCAG 2.1 AA", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)
      await searchCarteAndWaitForActeurs(page, "Auray")
      await clickFirstClickableActeurMarker(page)
      const panel = page.getByTestId("acteur-detail-about-panel")
      await expect(panel).toBeVisible()

      const results = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze()
      expect(results.violations).toEqual([])
    })

    test("La carte en mode liste avec résultats respecte WCAG 2.1 AA", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)
      await searchCarteAndWaitForActeurs(page, "Auray")
      await switchToListeMode(page)

      const results = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze()
      expect(results.violations).toEqual([])
    })
  })
})
