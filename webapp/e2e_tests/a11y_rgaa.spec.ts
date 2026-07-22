import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Site Que faire] 6.1 — Lien info-tri explicite", () => {
    test("Le title du lien info-tri reprend son intitulé visible", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/pages/produit/")
      const link = page.getByTestId("infotri-link")
      await expect(link).toBeVisible()
      const text = (await link.textContent())?.trim()
      const title = await link.getAttribute("title")
      expect(title).toBe(`${text} - Nouvelle fenêtre`)
    })
  })
})
