import { AxeBuilder } from "@axe-core/playwright"
import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * ⚠️ ATTENTION : Ce fichier est consolidé dans e2e_tests/a11y.spec.ts
 * depuis le 2026-06-15. Les tests ci-dessous sont conservés pour référence
 * mais les nouveaux tests d'accessibilité doivent être ajoutés dans a11y.spec.ts.
 *
 * Voir : improve-a11y-tests branch
 */

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
})
