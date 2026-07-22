import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 8.9 — Balise sémantique pour la date de mise à jour", () => {
    test("La date de mise à jour de la fiche acteur est dans une balise <p>", async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/pages/acteur/")
      const updatedDate = page.locator("p", { hasText: "Mis à jour le" })
      await expect(updatedDate).toBeVisible()
    })
  })
})
