import { expect, Page } from "@playwright/test"
import { test } from "./fixtures"
import { navigateTo, TIMEOUT } from "./helpers"

async function loginAsAdmin(page: Page) {
  await navigateTo(page, "/admin/login/")
  await page.getByRole("textbox", { name: "Nom d'utilisateur" }).fill("admin")
  await page.getByRole("textbox", { name: "Mot de passe" }).fill("admin")
  await page.getByRole("button", { name: "Connexion" }).click()
  await page.waitForURL("**/admin/")
}

test.describe("🛠️ Django Admin - Carte géographique", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  test("La carte s'affiche et est interactive sur la fiche d'un acteur", async ({
    page,
  }) => {
    await navigateTo(page, "/admin/qfdmo/revisionacteur/")

    // Click the first acteur in the list
    await page.locator("#result_list .field-nom a").first().click()

    await page.waitForLoadState("domcontentloaded")

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
})
