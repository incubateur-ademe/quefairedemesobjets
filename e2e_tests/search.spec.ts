import { expect, test } from "@playwright/test"
import { navigateTo, TIMEOUT } from "./helpers"

const searchTestCases = [
  {
    query: "lave",
    expectedResults: [
      "Façade de lave-vaisselle",
      "Lave-vaisselle",
      "Lave-linge",
      "Machine à laver",
      "Lavabo en résine",
      "Lavabo en céramique",
      "Rangement sous lavabo",
      "Spray répulsif anti-moustiques pour la peau",
      "Lame de terrasse composite",
      "Lame de terrasse en bois",
    ],
  },
  {
    query: "télé",
    expectedResults: [
      "Téléphone mobile",
      "Meuble de téléphone",
      "Téléviseur",
      "Télévision",
      "Carte à puce (bancaire, de téléphone, d'identité)",
      "Téléphone fixe",
      "Télécommande",
      "Jouet télécommandé",
      "Matériel d'athlétisme (haie, starting-block, bâton, témoin, javelot, poids, disque, marteau, matériel pour saut en longueur et hauteur…)",
      "Essence de térébenthine",
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
