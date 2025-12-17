import { expect, test } from "@playwright/test"
import { findViewModeLabel, openAdvancedFilters, searchDummyAdresse } from "./helpers"

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

test.describe("🗺️ Navigation Carte/Liste", () => {
  /**
   * Trouve le label d'un input radio dans le conteneur view-mode-nav avec le texte correspondant
   * On retourne le label car c'est lui qui doit être cliqué (il intercepte les événements)
   */

  test("Navigation entre carte et liste avec des résultats", async ({ page }) => {
    const url =
      "https://quefairedemesdechets.ademe.local/carte?map_container_id=carte&querystring=&adresse=Auray&longitude=-2.990838&latitude=47.668099&carte_view_mode-view=carte&carte_legende-groupe_action=1&carte_legende-groupe_action=2&carte_legende-groupe_action=3&carte_legende-groupe_action=4&carte_legende-groupe_action=5&carte=&r=236&bounding_box=&carte_filtres-synonyme=&carte_filtres-pas_exclusivite_reparation=on"

    // 1. Navigate to the URL
    await page.goto(url, {
      waitUntil: "domcontentloaded",
    })

    // 2. Verify that the carte is displayed with pinpoints
    // Wait for the carte to be loaded and that there are markers
    await page.waitForSelector(".maplibregl-marker:has(svg)", { timeout: 10000 })
    const markers = page.locator(".maplibregl-marker:has(svg)")
    await expect(markers.first()).toBeVisible()
    const markerCount = await markers.count()
    expect(markerCount).toBeGreaterThan(0)

    // 3. Click on the label "Liste"
    const listeLabel = await findViewModeLabel(page, "Liste")
    await listeLabel.click()

    // Wait for the list mode to be loaded
    await page.waitForSelector('main:has-text("Nom du lieu")', { timeout: 5000 })

    // 4. Verify that a table is displayed and that it is not empty
    // Wait for the list mode to be loaded with the table
    await page.waitForSelector('table:has(thead th:has-text("Nom du lieu"))', {
      timeout: 5000,
    })
    const table = page.locator("table")
    await expect(table).toBeVisible({ timeout: 5000 })

    // Verify that the table contains data rows (not only the header)
    const tableRows = table.locator("tbody tr")
    // Wait for at least one row to be present
    await expect(tableRows.first()).toBeVisible({ timeout: 5000 })
    const rowCount = await tableRows.count()
    expect(rowCount).toBeGreaterThan(0)

    // 5. Click on the label "Carte"
    const carteLabel = await findViewModeLabel(page, "Carte")
    await carteLabel.click()

    // Wait for the carte mode to be loaded
    await page.waitForSelector(".maplibregl-marker:has(svg)", { timeout: 5000 })

    // 6. Verify that the carte is displayed with pinpoints
    const markersAfterSwitch = page.locator(".maplibregl-marker:has(svg)")
    await expect(markersAfterSwitch.first()).toBeVisible()
    const markerCountAfterSwitch = await markersAfterSwitch.count()
    expect(markerCountAfterSwitch).toBeGreaterThan(0)
  })
})
