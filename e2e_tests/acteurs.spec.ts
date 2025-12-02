import { expect, test } from "@playwright/test"
import { getMarkers, mockApiAdresse } from "./helpers"
test.describe("🗺️ Affichage et Interaction Acteurs", () => {
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
