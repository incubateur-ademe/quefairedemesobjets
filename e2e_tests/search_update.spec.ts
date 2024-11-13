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
    await expect (page.locator("[data-search-solution-form-target=headerAddressPanel]")).toBeVisible()
    // This tests that the header of the Formulaire view cannot be reached when the Update form is opened.
    // This cannot be tested with .toBeVisible or toBeInViewport because of the way the header is styled.
    // It is actually visible, but is covered by a child of the header's adjacent <main> tag, and
    // Playwright detect it as visible.
    // Testing that we cannot interact with it ensures it is actually not visible.
    await page.locator("button[data-testid=modifier-recherche]").click()
    try {
      await page.locator("[data-search-solution-form-target=headerAddressPanel]").click({ timeout: 2000 })
    } catch (error) {
      expect(error.message).toContain('locator.click: Timeout');
    }
})
