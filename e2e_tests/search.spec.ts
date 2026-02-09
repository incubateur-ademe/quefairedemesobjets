import { expect, test } from "@playwright/test"
import { navigateTo, TIMEOUT } from "./helpers"

const searchTestCases = [
  {
    query: "lave",
    expectedResults: [
      "Lave-vaisselle",
      "Lave-linge",
      "Façade de lave-vaisselle",
      "Machine à laver",
      "Lame de terrasse composite",
      "Lame de terrasse en bois",
      "Lame d'arme blanche",
      "Cave à vin",
      "Lame de sécateur",
      "Lame de scie",
    ],
  },
  {
    query: "télé",
    expectedResults: [
      "Téléphone mobile",
      "Téléviseur",
      "Télévision",
      "Batterie de vélo électrique ou EDPM (draisienne, trottinette, gyroroue...)",
      "Tôle en métal",
      "Sacoche de vélo",
      "Transat de bain pour bébé",
      "Transat pour bébé",
      "Fauteuil bébé",
      "Vélo - hors vélo électrique",
    ],
  },
  {
    query: "chaise",
    expectedResults: [
      "Chaise pliante",
      "Chaise longue de jardin (fixe ou pliante)",
      "Chaise évolutive d'enfant",
      "Chaise haute",
      "Chaise d'enfant",
      "Chaise avec tablette",
      "Chaise de massage",
      "Chaise longue",
      "Chaise de jardin",
      "Chaise",
    ],
  },
]

test.describe("Recherche de produits", () => {
  for (const { query, expectedResults } of searchTestCases) {
    test(`La recherche "${query}" retourne les résultats attendus`, async ({
      page,
    }) => {
      await navigateTo(page, "/")

      const searchInput = page.locator("#id_home-input")
      await searchInput.click()
      await searchInput.pressSequentially(query, { delay: 50 })

      // Wait for search results to appear
      const resultsContainer = page.locator("[data-search-target='results'] a")
      await expect(resultsContainer.first()).toBeVisible({
        timeout: TIMEOUT.DEFAULT,
      })

      // Verify the number of results
      await expect(resultsContainer).toHaveCount(expectedResults.length)

      // Verify each result text matches in order
      for (let i = 0; i < expectedResults.length; i++) {
        await expect(resultsContainer.nth(i)).toHaveText(expectedResults[i])
      }
    })
  }
})
