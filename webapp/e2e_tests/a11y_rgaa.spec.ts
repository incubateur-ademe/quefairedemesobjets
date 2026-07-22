import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 9.1 — Niveau de titre des sections de la fiche acteur", () => {
    test("Les titres « Adresse » et « Services disponibles » sont des <h4>", async ({
      page,
    }) => {
      await navigateTo(
        page,
        "/lookbook/preview/accessibilite/A11Y_14_acteur_section_heading_level/",
      )
      const headings = page.locator("h4")
      await expect(headings.filter({ hasText: "Adresse" })).toBeAttached()
      await expect(headings.filter({ hasText: "Services disponibles" })).toBeAttached()
      await expect(page.locator("h3", { hasText: "Adresse" })).toHaveCount(0)
    })
  })
})
