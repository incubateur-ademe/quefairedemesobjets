import { expect, test } from "@playwright/test";
import { hideDjangoToolbar, searchDummyAdresse } from "./helpers";
function getItemSelector(index) {
  return `#mauvais_etat #id_adresseautocomplete-list.autocomplete-items div:nth-of-type(${index})`
}

test.describe("Tests de l'assistant", () => {
  test("Desktop | La carte s'affiche sur une fiche déchet/objet", async ({ page }) => {
    // Navigate to the carte page
    await page.goto(`/dechet/lave-linge`, { waitUntil: "networkidle" });
    await hideDjangoToolbar(page)
    const inputSelector = "#mauvais_etat input#id_adresse"
    const adresseFill = "Auray"
    // Autour de moi
    await page.locator(inputSelector).click();
    await page.locator(inputSelector).fill(adresseFill);
    expect(page.locator(getItemSelector(1)).innerText()).not.toBe("Autour de moi")
    await page.locator(getItemSelector(1)).click();
    const sessionStorage = await page.evaluate(() => window.sessionStorage)
    expect(sessionStorage.adresse).toBe(adresseFill)
    expect(sessionStorage.latitude).toContain("47.6")
    expect(sessionStorage.longitude).toContain("-2.9")

    await expect(page.getByTestId("map-marker").first()).toBeVisible()
    await page.getByTestId("map-marker").click()
    expect(page.locator("#acteurDetailsPanel")).toBeVisible()
  })
})
