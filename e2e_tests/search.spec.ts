import { expect, test } from "@playwright/test"
import { navigateTo, TIMEOUT } from "./helpers"

const searchTestCases = [
  {
    query: "lave",
    expectedResults: [
      "Lave-linge",
      "Lave-vaisselle",
      "Façade de lave-vaisselle",
      "Machine à laver",
      "Lavabo en résine",
      "Lavabo en céramique",
      "Rangement sous lavabo",
      "Article pour la pêche à la ligne",
      "Spray répulsif anti-moustiques pour la peau",
      "Bouée, planche, matériel d'aide à la flottaison",
    ],
  },
  {
    query: "télé",
    expectedResults: [
      "Téléphone fixe",
      "Téléphone mobile",
      "Meuble de téléphone",
      "Carte à puce (bancaire, de téléphone, d'identité)",
      "Téléviseur",
      "Télévision",
      "Télécommande",
      "Jouet télécommandé",
      "Matériel d'athlétisme (haie, starting-block, bâton, témoin, javelot, poids, disque, marteau, matériel pour saut en longueur et hauteur…)",
      "T-shirt",
    ],
  },
  {
    query: "chaise",
    expectedResults: [
      "Chaise",
      "Chaise haute",
      "Chaise longue",
      "Chaise pliante",
      "Chaise d'enfant",
      "Chaise de jardin",
      "Chaise de massage",
      "Chaise avec tablette",
      "Chaise évolutive d'enfant",
      "Chaise longue de jardin (fixe ou pliante)",
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
