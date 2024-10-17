import { expect, test } from "@playwright/test"

test("Recherche et modification d'une recherche", async ({ page }) => {
    await page.goto(`http://localhost:8000/`, {
        waitUntil: "networkidle",
    })
    // Masquage de django debug toolbar
    await page.locator("#djHideToolBarButton").click()



    await page.locator("input#id_sous_categorie_objet").click()
    await page.locator("input#id_sous_categorie_objet").fill("chaussures")
    await expect(page.locator("#id_sous_categorie_objetautocomplete-list")).toBeInViewport()
    await page.locator("#id_sous_categorie_objetautocomplete-list.autocomplete-items div:first-of-type").click()

    await page.locator("input#id_adresse").click()
    await page.locator("input#id_adresse").fill("10 rue de la paix")
    await expect (page.locator("#id_adresseautocomplete-list.autocomplete-items div:nth-of-type(2)")).toBeInViewport()
    await page.locator("#id_adresseautocomplete-list.autocomplete-items div:nth-of-type(2)").click()
    await page.locator("button[data-testid=rechercher-adresses-submit]").click()

    await expect (page.locator("[data-search-solution-form-target=headerAddressPanel]")).toBeInViewport()
    await page.locator("button[data-testid=modifier-recherche]").click()
    await expect (page.locator("[data-search-solution-form-target=headerAddressPanel]")).toBeHidden()
})
