import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 5.4 / 5.6 — Titre et en-têtes du tableau mode liste", () => {
    test("Le tableau a une légende (<caption>) non vide", async ({ page }) => {
      await navigateTo(
        page,
        "/lookbook/preview/accessibilite/A11Y_15_mode_liste_table_caption_et_entetes/",
      )
      const caption = page.locator("table caption")
      await expect(caption).toBeAttached()
      await expect(caption).not.toHaveText("")
    })

    test("La colonne « Voir la fiche » a un en-tête non vide", async ({ page }) => {
      await navigateTo(
        page,
        "/lookbook/preview/accessibilite/A11Y_15_mode_liste_table_caption_et_entetes/",
      )
      const headers = page.locator("table thead th")
      await expect(headers).toHaveCount(4)
      const lastHeader = headers.last()
      await expect(lastHeader).not.toHaveText("")
    })
  })
})
