import { test, expect } from "@playwright/test"
import { navigateTo, SEARCH_INPUT_SELECTOR } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Site Que faire] 10.12 — Espacement du texte du champ de recherche", () => {
    test("le champ de recherche n'est pas rogné avec un espacement de texte élargi (WCAG 1.4.12)", async ({
      page,
    }) => {
      await navigateTo(page, "/")
      await page.addStyleTag({
        content: `
          * {
            line-height: 1.5 !important;
            letter-spacing: 0.12em !important;
            word-spacing: 0.16em !important;
          }
          p {
            margin-bottom: 2em !important;
          }
        `,
      })
      const searchWrapper = page.locator(
        '[data-controller="search"]:has(' + SEARCH_INPUT_SELECTOR + ")",
      )
      const box = await searchWrapper.boundingBox()
      const input = page.locator(SEARCH_INPUT_SELECTOR)
      const inputBox = await input.boundingBox()
      expect(box).not.toBeNull()
      expect(inputBox).not.toBeNull()
      // The input row must not be clipped by its ancestor: the input's
      // bottom edge should stay within the wrapper's bounds.
      if (box && inputBox) {
        expect(inputBox.y + inputBox.height).toBeLessThanOrEqual(box.y + box.height + 1)
      }
    })
  })
})
