import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 6.1 — Liens explicites (ajouter un lieu)", () => {
    test('Le bouton "ajouter un lieu" a un aria-label cohérent avec son texte visible', async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/carte/ajouter_un_lieu/")
      const link = page.locator("a").first()
      const text = (await link.textContent())?.trim()
      const ariaLabel = await link.getAttribute("aria-label")
      expect(ariaLabel).toBe(`${text} - Nouvelle fenêtre`)
    })
    // Le title des liens de partage (Facebook, X, LinkedIn, email) est
    // couvert par integration_tests/core/test_sharer.py, la preview
    // Lookbook du tooltip de partage n'ayant pas de request.resolver_match
    // pour générer le sharer réel.
  })
})
