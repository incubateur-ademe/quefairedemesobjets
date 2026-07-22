import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Site Que faire] 6.1 — Lien logo header explicite sur la carte", () => {
    test('Le lien logo du header carte expose un libellé "Accueil — ..."', async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      const logoLink = page.locator("#logo a[href='/']").first()
      await expect(logoLink).toHaveAccessibleName(/Accueil — /)
    })
  })
})
