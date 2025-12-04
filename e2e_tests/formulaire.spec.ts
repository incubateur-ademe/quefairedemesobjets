import { expect, test } from "@playwright/test"
import {
  mockApiAdresse,
  searchDummyAdresse,
  searchDummySousCategorieObjet,
  openAdvancedFilters,
} from "./helpers"

test.describe("🔍 Recherche et Modification Formulaire", () => {
  test("Recherche et modification d'une recherche", async ({ page }) => {
    // Helper function to handle autocomplete inputs

    // Navigate to the formulaire page
    await page.goto(`/formulaire`, { waitUntil: "domcontentloaded" })

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
test.describe("📝 Liste d'Actions Formulaire", () => {
  test("Action list by default", async ({ page }) => {
    await page.goto(`/formulaire`, {
      waitUntil: "domcontentloaded",
    })

    const id_action_list1 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list1).toBe(
      "preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre",
    )
  })

  test("Action list is well set with jai", async ({ page }) => {
    await page.goto(`/formulaire?direction=jai&action_list=preter`, {
      waitUntil: "domcontentloaded",
    })

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

  test("Action list is well set with jecherche", async ({ page }) => {
    await page.goto(`/formulaire?direction=jecherche&action_list=emprunter`, {
      waitUntil: "domcontentloaded",
    })

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

test.skip("Filtres avancés s'ouvrent et se ferment en mode formulaire", async ({
  page,
}) => {
  await page.goto(`/formulaire`, {
    waitUntil: "domcontentloaded",
  })
  await openAdvancedFilters(page)
})

test.skip("Les acteurs digitaux sont visibles sur le formulaire", async ({ page }) => {
  // Navigate to the lookbook preview page
  await page.goto(`/lookbook/preview/iframe/formulaire/`, {
    waitUntil: "domcontentloaded",
  })

  const iframe = page.frameLocator("iframe#formulaire")
  await mockApiAdresse(page)
  // Fill "Sous catégorie objet" autocomplete input
  await searchDummySousCategorieObjet(page)

  // Fill "Adresse" autocomplete input
  await searchDummyAdresse(page)

  // Submit the search form
  await page
    .locator("button[data-testid=formulaire-rechercher-adresses-submit]")
    .click()

  const someLeafletMarker = iframe.locator(".maplibregl-marker").first()
  await expect(someLeafletMarker).toBeAttached()

  // Digital acteurs
  await iframe.locator("#id_digital_1").click({ force: true })
  await iframe.locator("[aria-controls=acteurDetailsPanel]").first().click()
  await expect(iframe.locator("#acteurDetailsPanel")).toHaveAttribute(
    "aria-hidden",
    "false",
  )
})
test.skip("🗺️ Affichage et Interaction Acteurs", () => {
  test("Les acteurs sont visibles sur la carte du formulaire et fonctionnent", async ({
    page,
  }) => {
    // Navigate to the lookbook preview page
    await page.goto(`/lookbook/preview/iframe/formulaire/`, {
      waitUntil: "domcontentloaded",
    })

    // Use frameLocator for better iframe handling
    const iframe = page.frameLocator("iframe#formulaire")

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
    inputSelector = "#id_adresse"
    await iframe.locator(inputSelector).click()
    await mockApiAdresse(page)
    await iframe.locator(inputSelector).fill("auray")
    await iframe
      .locator("#id_adresseautocomplete-list.autocomplete-items div:nth-child(1)")
      .click()

    // Submit form
    await iframe.getByTestId("formulaire-rechercher-adresses-submit").click()

    // Remove the home marker (red dot) that prevents Playwright from clicking other markers
    const markers = iframe.locator(".maplibregl-marker")
    // const count = await markers.count()

    await page.waitForLoadState("networkidle")

    const count = await markers.count()
    for (let i = 0; i < count; i++) {
      const item = markers.nth(i)
      try {
        await item.click({ force: true })
        break
      } catch (e) {
        console.log(`Cannot click marker ${i}:`, e)
      }
    }

    // Wait for the panel to be shown (aria-hidden="false")
    await expect(iframe.locator("#acteurDetailsPanel")).toHaveAttribute(
      "aria-hidden",
      "false",
    )
  })
})
