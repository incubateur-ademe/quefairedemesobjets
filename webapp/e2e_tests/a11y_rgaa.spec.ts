import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 1.2 — Logo décoratif dans les onglets Labels/Sources", () => {
    test("Le logo précédant un label/source a un alt vide", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/pages/acteur/")
      const logoImg = page.locator('img[src*="/media/logos/"], img[src*="/logos/"]')
      const count = await logoImg.count()
      if (count > 0) {
        await expect(logoImg.first()).toHaveAttribute("alt", "")
      }
    })
  })
})
