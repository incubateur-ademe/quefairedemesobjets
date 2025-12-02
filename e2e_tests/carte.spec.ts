import { expect, test } from "@playwright/test"
import { openAdvancedFilters, searchDummyAdresse } from "./helpers"

test.describe("🗺️ Filtres Avancés Carte", () => {
  async function searchInCarteMode(page) {
    await page.locator("input#id_adresse").click()
    await page.locator("input#id_adresse").fill("Paris")
    await page
      .locator("#id_adresseautocomplete-list.autocomplete-items div:nth-of-type(2)")
      .click()
  }

  test("Filtres avancés s'ouvrent et se ferment en mode carte", async ({ page }) => {
    await page.goto(`/carte`, {
      waitUntil: "domcontentloaded",
    })
    await searchInCarteMode(page)
    await openAdvancedFilters(
      page,
      "carte-legend",
      "modal-button-carte:filtres",
      "modal-carte:filtres",
    )
  })

  test(
    "Filtres avancés s'ouvrent et se ferment en mode carte en mobile",
    { tag: ["@mobile"] },
    async ({ page }) => {
      await page.goto(`/carte`, {
        waitUntil: "domcontentloaded",
      })
      await searchInCarteMode(page)
      await openAdvancedFilters(page)
    },
  )
})
test.describe("🗺️ Affichage Légende Carte", () => {
  test("La carte affiche la légende après une recherche", async ({ page }) => {
    // Navigate to the carte page
    await page.goto(`/carte`, { waitUntil: "domcontentloaded" })

    await expect(page.getByTestId("carte-legend")).toBeHidden()

    // Fill "Adresse" autocomplete input
    await searchDummyAdresse(page)
    await expect(page.getByTestId("carte-legend")).toBeVisible()
  })
})
