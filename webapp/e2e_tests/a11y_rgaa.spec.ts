import { test, expect } from "@playwright/test"
import { navigateTo, switchToListeMode } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 10.8 — Alternative textuelle pour l'illustration mode liste vide", () => {
    test("Le mode liste sans résultat a une alternative textuelle pour les technologies d'assistance", async ({
      page,
    }) => {
      // Bounding box en pleine mer : garantit l'absence de résultat.
      await navigateTo(
        page,
        '/carte?bounding_box={"southWest":{"lat":0,"lng":0},"northEast":{"lat":1,"lng":1}}',
      )
      await switchToListeMode(page)
      const alt = page.getByText("Aucun résultat trouvé pour votre recherche.")
      await expect(alt).toBeAttached()
    })
  })
})
