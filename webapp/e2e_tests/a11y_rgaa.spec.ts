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
