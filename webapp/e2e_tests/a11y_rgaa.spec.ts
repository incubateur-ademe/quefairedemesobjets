import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Site Que faire] 1.2 — Image info-tri décorative ignorée", () => {
    test("L'image info-tri a un alt vide", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/pages/produit/")
      const infotriImg = page.locator(".qf-h-\\[80px\\] img")
      await expect(infotriImg.first()).toHaveAttribute("alt", "")
    })
  })
})
