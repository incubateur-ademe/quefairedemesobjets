import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Site Que faire] 12.7 — Lien d'évitement fonctionnel (bug Firefox)", () => {
    for (const path of ["/", "/carte"]) {
      test(`Le <main id="content"> de ${path} porte tabindex="-1"`, async ({
        page,
      }) => {
        await navigateTo(page, path)
        const main = page.locator("main#content")
        await expect(main).toHaveAttribute("tabindex", "-1")
      })
    }

    test('Le <nav id="fr-navigation"> porte tabindex="-1" quand il est rendu', async ({
      page,
    }) => {
      await navigateTo(page, "/")
      const nav = page.locator("nav#fr-navigation")
      const count = await nav.count()
      if (count > 0) {
        await expect(nav).toHaveAttribute("tabindex", "-1")
      }
    })
  })
})
