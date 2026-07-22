import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 11.6 — Légende du toggle Carte/Liste", () => {
    test("Le fieldset du toggle Carte/Liste a une légende « Mode d'affichage »", async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/formulaires/mode_carte_liste/")
      const legend = page.locator(".fr-segmented__legend")
      await expect(legend).toHaveText(/Mode d'affichage/)
    })
  })

  test.describe("[Carte] 11.7 — Légende pertinente dans la modale filtres", () => {
    test('La légende du groupe de labels/certifications n\'est pas juste "Optional"', async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/modals/filtres/")
      const legend = page.locator("#id_label_qualite-legend")
      await expect(legend).toContainText("Labels et certifications")
    })
  })
})
