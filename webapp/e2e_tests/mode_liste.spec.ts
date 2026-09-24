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
    await mockApiAdresse(page)
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

test.describe("Score de conversion en mode liste", () => {
  // The analytics controller mirrors the conversion score into sessionStorage
  // each time it changes, which is also what triggers the PostHog "$set" event.
  const mapInteractions = (page) =>
    page.evaluate(() => Number(sessionStorage.getItem("userInteractionWithMap") ?? 0))

  test("Ouvrir un lieu depuis la liste compte comme une interaction avec la carte", async ({
    page,
  }) => {
    await mockApiAdresse(page)
    await navigateTo(page, "/carte")
    await searchCarteAndWaitForActeurs(page, "auray")
    await switchToListeMode(page)

    const before = await mapInteractions(page)

    await page.getByTestId("acteur-list-link").first().click()
    await expect.poll(() => mapInteractions(page)).toBe(before + 1)

    await page.getByTestId("voir-la-fiche").first().click()
    await expect.poll(() => mapInteractions(page)).toBe(before + 2)
  })
})
