import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 8.6 — Titre de page pertinent", () => {
    test("La page carte a un titre mentionnant « carte interactive »", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      await expect(page).toHaveTitle(/carte interactive/i)
    })
  })
})
