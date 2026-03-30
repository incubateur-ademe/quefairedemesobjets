import { expect } from "@playwright/test"
import { test } from "./fixtures"
import {
  clickFirstClickableActeurMarker,
  getIframe,
  mockApiAdresse,
  navigateTo,
  searchCarteAndWaitForActeurs,
  searchOnProduitPage,
  switchToListeMode,
  TIMEOUT,
} from "./helpers"

test.describe("Mode liste", () => {
  test("Le mode liste affiche la distance", async ({ page }) => {
    await navigateTo(page, "/carte")

    await searchCarteAndWaitForActeurs(page, "auray")
    await switchToListeMode(page)
    const liste = page.locator(".fr-table--mode-liste")
    const distanceCellOnFirstRow = liste
      .locator("tbody tr:first-of-type td:nth-of-type(3)")
      .first()
    const text = await distanceCellOnFirstRow.textContent()
    expect(text?.trim().endsWith("m")).toBe(true)
  })
})
