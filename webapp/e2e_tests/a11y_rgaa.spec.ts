import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 7.2 / 12.8 / 12.11 — Tooltip de partage nettoyé", () => {
    test('Le tooltip de partage n\'a pas de tabindex positif, ni role="toolbar", ni aria-describedby', async ({
      page,
    }) => {
      await navigateTo(
        page,
        "/lookbook/preview/accessibilite/share_tooltip_acteur_sans_tabindex/",
      )
      const shareButton = page.locator('button:has(span:text("partager"))')
      await expect(shareButton).not.toHaveAttribute("aria-describedby", /.+/)

      const tooltip = page.locator(".fr-tooltip")
      await expect(tooltip).not.toHaveAttribute("tabindex", "1")

      const shareToolbar = page.locator(".fr-share")
      await expect(shareToolbar).not.toHaveAttribute("role", "toolbar")
    })
  })
})
