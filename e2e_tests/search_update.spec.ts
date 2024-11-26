import { expect, test } from "@playwright/test"
import { hideDjangoToolbar, searchDummyAdresse, searchDummySousCategorieObjet } from "./helpers"

test("Recherche et modification d'une recherche", async ({ page }) => {
  // Helper function to handle autocomplete inputs

  // Navigate to the formulaire page
  await page.goto(`http://localhost:8000/formulaire`, { waitUntil: "networkidle" })

  // Hide the Django debug toolbar
  await hideDjangoToolbar(page)

  // Expect the Proposer une adresse button to be hidden
  await expect(page.getByTestId("formulaire-proposer-une-adresse")).not.toBeVisible()

  // Fill "Sous catégorie objet" autocomplete input
  await searchDummySousCategorieObjet(page)

  // Fill "Adresse" autocomplete input
  await searchDummyAdresse(page)

  // Submit the search form
  await page.locator("button[data-testid=rechercher-adresses-submit]").click()

  // Expect the Proposer une adresse button to be visible
  await expect(page.getByTestId("formulaire-proposer-une-adresse")).toBeVisible()

  // Verify the search header is displayed
  await expect(
    page.locator("[data-search-solution-form-target=headerAddressPanel]"),
  ).toBeVisible()

  // Open the modification form
  await page.locator("button[data-testid=modifier-recherche]").click()

  // Verify the header cannot be interacted with
  // This weird tests is explained in https://github.com/incubateur-ademe/quefairedemesobjets/issues/1020
  try {
    const headerLocator = page.locator(
      "[data-search-solution-form-target=headerAddressPanel]",
    )
    await headerLocator.click({ timeout: 2000 })
  } catch (error) {
    expect(error.message).toContain("locator.click: Timeout")
  }
})
