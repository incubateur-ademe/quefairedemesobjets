import { expect, test } from "@playwright/test"
import {
  mockApiAdresse,
  searchDummyAdresse,
  searchDummySousCategorieObjet,
  openAdvancedFilters,
  navigateTo,
  searchAddress,
  searchAndSelectAutocomplete,
  getIframe,
  clickFirstAvailableMarker,
  TIMEOUT,
} from "./helpers"

test.describe("🔍 Formulaire de Recherche", () => {
  test("La recherche peut être effectuée puis modifiée", async ({ page }) => {
    // Helper function to handle autocomplete inputs

    // Navigate to the formulaire page
    await navigateTo(page, `/formulaire`)

    // Expect the Proposer une adresse button to be hidden
    await expect(page.getByTestId("formulaire-proposer-une-adresse")).not.toBeVisible()

    // Fill "Sous catégorie objet" autocomplete input
    await searchDummySousCategorieObjet(page)

    // Fill "Adresse" autocomplete input
    await searchDummyAdresse(page)

    // Submit the search form
    await page
      .locator("button[data-testid=formulaire-rechercher-adresses-submit]")
      .click()

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
})
test.describe("📝 Sélection d'Actions dans le Formulaire", () => {
  test("La liste d'actions par défaut contient toutes les actions", async ({
    page,
  }) => {
    await navigateTo(page, `/formulaire`)

    const id_action_list1 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list1).toBe(
      "preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre",
    )
  })

  test("Les actions sélectionnées dans la section 'J'ai' sont correctement ajoutées/retirées", async ({
    page,
  }) => {
    await navigateTo(page, `/formulaire?direction=jai&action_list=preter`)

    const id_action_list1 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list1).toBe("preter")

    // Select "jai" option
    await page.check("[value=jai]")

    // Assuming "action1" and "action2" are ids of checkboxes inside "jaiTarget"
    // Check these checkboxes
    await page.click('label[for="jai_reparer"]')

    // Expect id_action_list to be "reparer"
    const id_action_list2 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list2).toBe("preter|reparer")
  })

  test("Les actions sélectionnées dans la section 'Je cherche' sont correctement ajoutées/retirées", async ({
    page,
  }) => {
    await navigateTo(page, `/formulaire?direction=jecherche&action_list=emprunter`)

    // check that the action list is well set by default
    const id_action_list1 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list1).toBe("emprunter")

    // Assuming "action1" and "action2" are ids of checkboxes inside "jaiTarget"
    // Check these checkboxes
    await page.click('label[for="jecherche_emprunter"]')
    await page.click('label[for="jecherche_louer"]')

    // Expect id_action_list to be "reparer"
    const id_action_list2 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list2).toBe("louer")
  })
})

test("Filtres avancés s'ouvrent et se ferment en mode formulaire", async ({ page }) => {
  await navigateTo(page, `/formulaire`)
  await openAdvancedFilters(page)
})

// FIXME: This test requires digital acteur data in the test database
// Currently returns "Aucune solution en ligne n'a été trouvée pour votre recherche"
// Need to seed digital acteur test data that matches: Perceuse + Auray + actions (mettreenlocation, reparer, echanger, revendre)
test.skip("Les acteurs digitaux sont visibles sur le formulaire", async ({ page }) => {
  // Navigate directly to formulaire with search parameters that return digital acteurs
  await navigateTo(
    page,
    `/formulaire?map_container_id=formulaire&digital=digital&r=179&bounding_box=&direction=jai&action_displayed=preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre&action_list=mettreenlocation|reparer|echanger|revendre&sous_categorie_objet=Perceuse&sc_id=263&adresse=Auray&latitude=47.668099&longitude=-2.990838&mettreenlocation=on&reparer=on&echanger=on&echanger=on&revendre=on&emprunter=on&louer=on&acheter=on&pas_exclusivite_reparation=on`,
  )

  // Wait for digital acteurs results to appear
  await expect(page.locator('[data-testid="digital-acteurs-results"]')).toBeVisible({
    timeout: TIMEOUT.DEFAULT,
  })

  // Verify at least one digital acteur is displayed
  await expect(page.locator("[aria-controls=acteurDetailsPanel]").first()).toBeVisible({
    timeout: TIMEOUT.DEFAULT,
  })

  // Click on first digital acteur
  await page.locator("[aria-controls=acteurDetailsPanel]").first().click()

  // Verify details panel opens
  await expect(page.locator("#acteurDetailsPanel")).toHaveAttribute(
    "aria-hidden",
    "false",
  )
})

test.describe("🗺️ Affichage et Interaction Acteurs", () => {
  // FIXME: This test requires test data with acteurs near the searched address
  test("Les acteurs sont visibles sur la carte du formulaire et fonctionnent", async ({
    page,
  }) => {
    // Navigate to the lookbook preview page
    await navigateTo(page, `/lookbook/preview/iframe/formulaire/`)

    // Use frameLocator for better iframe handling
    const iframe = getIframe(page, "formulaire")

    // Select a Produit
    let inputSelector = "#id_sous_categorie_objet"
    await iframe.locator(inputSelector).click()
    await iframe.locator(inputSelector).fill("perceuse")
    await iframe
      .locator(
        "#id_sous_categorie_objetautocomplete-list.autocomplete-items div:nth-child(1)",
      )
      .click()

    // Fill adresse
    await mockApiAdresse(page)
    await searchAddress(iframe, "auray", "formulaire")

    // Submit form
    await iframe.getByTestId("formulaire-rechercher-adresses-submit").click()

    // Wait for markers to appear on the map
    await expect(iframe.locator(".maplibregl-marker").first()).toBeVisible({
      timeout: TIMEOUT.LONG,
    })

    await clickFirstAvailableMarker(iframe, ".maplibregl-marker")

    // Wait for the panel to be shown (aria-hidden="false")
    await expect(iframe.locator("#acteurDetailsPanel")).toHaveAttribute(
      "aria-hidden",
      "false",
      { timeout: TIMEOUT.LONG },
    )
  })
})
