import { expect, test } from "@playwright/test";

test("Recherche et modification d'une recherche", async ({ page }) => {
    // Helper function to handle autocomplete inputs
    const fillAndSelectAutocomplete = async (inputSelector, inputText, itemSelector) => {
        await page.locator(inputSelector).click();
        await page.locator(inputSelector).fill(inputText);
        await expect(page.locator(itemSelector)).toBeInViewport();
        await page.locator(itemSelector).click();
    };

    // Navigate to the formulaire page
    await page.goto(`http://localhost:8000/formulaire`, { waitUntil: "networkidle" });

    // Hide the Django debug toolbar
    await page.locator("#djHideToolBarButton").click();

    // Expect the Proposer une adresse button to be hidden
    await expect(page.getByTestId("formulaire-proposer-une-adresse")).not.toBeVisible()

    // Fill "Sous catégorie objet" autocomplete input
    await fillAndSelectAutocomplete(
        "input#id_sous_categorie_objet",
        "chaussures",
        "#id_sous_categorie_objetautocomplete-list.autocomplete-items div:first-of-type"
    );

    // Fill "Adresse" autocomplete input
    await fillAndSelectAutocomplete(
        "input#id_adresse",
        "10 rue de la paix",
        "#id_adresseautocomplete-list.autocomplete-items div:nth-of-type(2)"
    );

    // Submit the search form
    await page.locator("button[data-testid=rechercher-adresses-submit]").click();

    // Expect the Proposer une adresse button to be visible
    await expect(page.getByTestId("formulaire-proposer-une-adresse")).toBeVisible()

    // Verify the search header is displayed
    await expect(page.locator("[data-search-solution-form-target=headerAddressPanel]")).toBeVisible();

    // Open the modification form
    await page.locator("button[data-testid=modifier-recherche]").click();

    // Verify the header cannot be interacted with
    // This weird tests is explained in https://github.com/incubateur-ademe/quefairedemesobjets/issues/1020
    try {
      const headerLocator = page.locator("[data-search-solution-form-target=headerAddressPanel]");
      await headerLocator.click({ timeout: 2000 })
    } catch (error) {
      expect(error.message).toContain('locator.click: Timeout');
    }

});
