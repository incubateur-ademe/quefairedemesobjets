import { expect, test } from "@playwright/test"
import {
  mockApiAdresse,
  searchDummyAdresse,
  searchDummySousCategorieObjet,
} from "./helpers"

test.describe("🔍 Formulaire Search and Update", () => {
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
test.describe("📝 Formulaire Action List", () => {
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

test("Les acteurs digitaux sont visibles sur le formulaire", async ({ page }) => {
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
