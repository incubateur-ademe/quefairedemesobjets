import { expect, Page } from "@playwright/test"
import { test } from "./fixtures"
import { navigateTo, TIMEOUT } from "./helpers"

async function loginAsAdmin(page: Page) {
  await navigateTo(page, "/admin/login/")
  await page.locator('input[name="username"]').fill("admin")
  await page.locator('input[name="password"]').fill("admin")
  await page.locator('[type="submit"]').click()
  await page.waitForURL("**/admin/")
}

async function openFirstActeur(page: Page) {
  await navigateTo(page, "/admin/qfdmo/displayedacteur/")
  await page.locator("#result_list .field-nom a").first().click()
  await page.waitForLoadState("domcontentloaded")
}

/** Read the current textarea value and parse it as GeoJSON coordinates */
async function readCoordinates(page: Page): Promise<[number, number]> {
  const raw = await page.locator(".vSerializedField").inputValue()
  const parsed = JSON.parse(raw)
  return parsed.coordinates as [number, number]
}

test.describe("🛠️ Django Admin - Carte géographique", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  test("La carte s'affiche et est interactive sur la fiche d'un acteur", async ({
    page,
  }) => {
    await openFirstActeur(page)

    // The map wrapper should be present
    const mapWrapper = page.locator(".dj_map_wrapper")
    await expect(mapWrapper).toBeVisible({ timeout: TIMEOUT.DEFAULT })

    // OpenLayers should have rendered a canvas inside the map div
    const mapCanvas = page.locator(".dj_map canvas")
    await expect(mapCanvas).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    // The serialized coordinates textarea should contain valid GeoJSON
    const textarea = page.locator(".vSerializedField")
    const value = await textarea.inputValue()
    expect(value).toContain('"type": "Point"')
    expect(value).toContain('"coordinates"')

    // The widget instance should be registered in the JS registry
    const isRegistered = await page.evaluate(() => {
      const textarea = document.querySelector<HTMLTextAreaElement>(".vSerializedField")
      if (!textarea) return false
      return !!(
        (window as any).geodjangoWidgets &&
        (window as any).geodjangoWidgets[textarea.id]
      )
    })
    expect(isRegistered).toBe(true)

    // Clicking "Supprimer toutes les localisations" should clear the value
    await page.locator(".clear_features a").click()
    const clearedValue = await textarea.inputValue()
    expect(clearedValue).toBe("")
  })

  test("Déplacer le marqueur sur la carte met à jour les coordonnées dans la textarea", async ({
    page,
  }) => {
    await openFirstActeur(page)

    const textarea = page.locator(".vSerializedField")
    await expect(textarea).not.toHaveValue("", { timeout: TIMEOUT.DEFAULT })

    const before = await readCoordinates(page)

    // Move the feature via the OpenLayers JS API, simulating what a drag does.
    // This is equivalent to what OL's Modify interaction does after a drag gesture.
    await page.evaluate(() => {
      const ta = document.querySelector<HTMLTextAreaElement>(".vSerializedField")!
      const widget = (window as any).geodjangoWidgets[ta.id]
      const features = widget.featureOverlay.getSource().getFeatures()
      if (!features.length) throw new Error("No features on map")
      const geom = features[0].getGeometry()
      const coords = geom.getCoordinates()
      // Shift by ~1 km in projected coordinates (EPSG:3857)
      geom.setCoordinates([coords[0] + 1000, coords[1] + 1000])
    })

    // serializeFeatures is called by the geometry 'change' event — wait for textarea update
    await expect(textarea).not.toHaveValue(
      JSON.stringify({ type: "Point", coordinates: before }),
      {
        timeout: TIMEOUT.DEFAULT,
      },
    )

    const after = await readCoordinates(page)
    // Coordinates should have shifted
    expect(after[0]).not.toBeCloseTo(before[0], 3)
  })

  test("La recherche d'adresse met à jour la carte et la textarea", async ({
    page,
  }) => {
    // Mock the geocoding API to avoid a real network call
    await page.route("**/geocodage/search/**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          features: [
            {
              geometry: { coordinates: [2.3469, 48.8592], type: "Point" },
            },
          ],
        }),
      })
    })

    await openFirstActeur(page)

    // Clear the current position first
    await page.locator(".clear_features a").click()
    await expect(page.locator(".vSerializedField")).toHaveValue("")

    // The search input should be present (rendered by the Stimulus controller)
    const searchInput = page.locator('[data-map-search-target="input"]')
    await expect(searchInput).toBeVisible({ timeout: TIMEOUT.DEFAULT })

    await searchInput.fill("Mairie de Paris")
    await page.locator('[data-action="click->map-search#search"]').click()

    // The textarea should now contain GeoJSON with the mocked coordinates
    await expect(page.locator(".vSerializedField")).not.toHaveValue("", {
      timeout: TIMEOUT.DEFAULT,
    })

    const [lon, lat] = await readCoordinates(page)
    expect(lon).toBeCloseTo(2.3469, 3)
    expect(lat).toBeCloseTo(48.8592, 3)
  })
})
