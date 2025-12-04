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
      await openAdvancedFilters(
        page,
        "view-mode-nav",
        "modal-button-carte:filtres",
        "modal-carte:filtres",
      )
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

test.describe("🗺️ Pinpoint Active State", () => {
  test("Clicking a pinpoint adds active class and removes it from other pinpoints", async ({
    page,
  }) => {
    // Navigate to the preview page with multiple pinpoints
    await page.goto(`/lookbook/preview/components/acteur_pinpoint_multiple`, {
      waitUntil: "domcontentloaded",
    })

    const pinpoint1 = page.getByTestId("pinpoint-1").locator("a")
    const pinpoint2 = page.getByTestId("pinpoint-2").locator("a")

    // Initially, no pinpoint should have the active class
    await expect(pinpoint1).not.toHaveClass(/active-pinpoint/)
    await expect(pinpoint2).not.toHaveClass(/active-pinpoint/)

    // Click on first pinpoint
    await pinpoint1.click()
    await expect(pinpoint1).toHaveClass(/active-pinpoint/)
    await expect(pinpoint2).not.toHaveClass(/active-pinpoint/)

    // Click on second pinpoint
    await pinpoint2.click()
    await expect(pinpoint1).not.toHaveClass(/active-pinpoint/)
    await expect(pinpoint2).toHaveClass(/active-pinpoint/)

    // Click on first pinpoint again
    await pinpoint1.click()
    await expect(pinpoint1).toHaveClass(/active-pinpoint/)
    await expect(pinpoint2).not.toHaveClass(/active-pinpoint/)
  })
})
