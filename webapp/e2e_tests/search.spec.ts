import { expect, test } from "@playwright/test"
import { navigateTo, TIMEOUT } from "./helpers"

const SEARCH_INPUT_SELECTOR = "#id_home-input"
const SEARCH_RESULTS_SELECTOR = "[data-search-target='results'] a"

async function typeSearchQuery(page, query: string) {
  const searchInput = page.locator(SEARCH_INPUT_SELECTOR)
  await searchInput.click()
  await searchInput.fill("")
  await searchInput.pressSequentially(query, { delay: 50 })
}

async function waitForResults(page) {
  const results = page.locator(SEARCH_RESULTS_SELECTOR)
  await expect(results.first()).toBeVisible({ timeout: TIMEOUT.DEFAULT })
  return results
}

test.describe("Recherche de produits", () => {
  test.beforeEach(async ({ page }) => {
    await navigateTo(page, "/")
  })

  test("La recherche affiche des résultats pertinents", async ({ page }) => {
    await typeSearchQuery(page, "lave")
    const results = await waitForResults(page)

    const count = await results.count()
    expect(count).toBeGreaterThan(0)
    expect(count).toBeLessThanOrEqual(10)

    // Les premiers résultats doivent contenir le terme recherché
    // ou être sémantiquement liés
    const firstResultText = await results.first().textContent()
    expect(firstResultText).toBeTruthy()
  })

  test("La recherche avec accents retourne des résultats", async ({ page }) => {
    await typeSearchQuery(page, "télé")
    const results = await waitForResults(page)

    const count = await results.count()
    expect(count).toBeGreaterThan(0)
    expect(count).toBeLessThanOrEqual(10)
  })

  test("Les résultats sont des liens cliquables", async ({ page }) => {
    await typeSearchQuery(page, "chaise")
    const results = await waitForResults(page)

    const count = await results.count()
    expect(count).toBeGreaterThan(0)

    // Chaque résultat est un lien avec un href non vide
    for (let i = 0; i < count; i++) {
      const href = await results.nth(i).getAttribute("href")
      expect(href).toBeTruthy()
    }
  })

  test("Cliquer sur un résultat navigue vers la page produit", async ({ page }) => {
    await typeSearchQuery(page, "lave")
    const results = await waitForResults(page)

    const firstResultHref = await results.first().getAttribute("href")
    expect(firstResultHref).toBeTruthy()

    await results.first().click()
    await page.waitForURL((url) => url.pathname !== "/", {
      timeout: TIMEOUT.DEFAULT,
    })

    // On est bien sur une page produit (URL /dechet/... ou page Wagtail)
    expect(page.url()).not.toBe("/")
  })

  test("La recherche se met à jour en temps réel", async ({ page }) => {
    // Taper une première requête
    await typeSearchQuery(page, "chaise")
    const firstResults = await waitForResults(page)
    const firstResultText = await firstResults.first().textContent()

    // Effacer et attendre que les résultats disparaissent
    const searchInput = page.locator(SEARCH_INPUT_SELECTOR)
    await searchInput.fill("")
    const results = page.locator(SEARCH_RESULTS_SELECTOR)
    await expect(results).toHaveCount(0, { timeout: TIMEOUT.DEFAULT })

    // Taper une autre requête
    await searchInput.pressSequentially("vélo", { delay: 50 })
    const newResults = await waitForResults(page)

    // Les résultats doivent être différents
    const newFirstResultText = await newResults.first().textContent()
    expect(newFirstResultText).not.toBe(firstResultText)
  })

  test("La recherche vide ne retourne pas de résultats", async ({ page }) => {
    const searchInput = page.locator(SEARCH_INPUT_SELECTOR)
    await searchInput.click()
    await searchInput.fill("")
    await searchInput.press("Enter")

    // Aucun résultat ne devrait être visible
    const results = page.locator(SEARCH_RESULTS_SELECTOR)
    await expect(results).toHaveCount(0)
  })

  test("Les résultats retournent un maximum de 10 éléments", async ({ page }) => {
    await typeSearchQuery(page, "a")
    const results = await waitForResults(page)
    const count = await results.count()
    expect(count).toBeLessThanOrEqual(10)
  })

  test("La navigation clavier fonctionne dans les résultats", async ({ page }) => {
    await typeSearchQuery(page, "lave")
    await waitForResults(page)

    // Naviguer vers le bas avec la flèche
    await page.keyboard.press("ArrowDown")

    // Le premier résultat doit avoir le focus
    const firstResult = page.locator(SEARCH_RESULTS_SELECTOR).first()
    await expect(firstResult).toBeFocused()

    // Naviguer encore vers le bas
    await page.keyboard.press("ArrowDown")
    const secondResult = page.locator(SEARCH_RESULTS_SELECTOR).nth(1)
    await expect(secondResult).toBeFocused()
  })

  test("Échap ferme les résultats de recherche", async ({ page }) => {
    await typeSearchQuery(page, "chaise")
    await waitForResults(page)

    await page.keyboard.press("Escape")

    // Les résultats ne devraient plus être visibles
    const results = page.locator(SEARCH_RESULTS_SELECTOR)
    await expect(results).toHaveCount(0, { timeout: TIMEOUT.SHORT })
  })

  test("Les liens des résultats SearchTag contiennent search_term_id, position et search_term", async ({
    page,
  }) => {
    await typeSearchQuery(page, "canapé d'angle")
    const results = await waitForResults(page)

    const count = await results.count()
    expect(count).toBeGreaterThan(0)

    // Parcourir les résultats et vérifier les liens qui contiennent search_term_id
    // (seuls les résultats de type SearchTag ont ces paramètres)
    let searchTagFound = false
    let nextUrl = ""
    for (let i = 0; i < count; i++) {
      const href = await results.nth(i).getAttribute("href")
      if (href && href.includes("search_term_id=")) {
        searchTagFound = true
        const url = new URL(href, "http://localhost")

        // search_term_id doit être un nombre
        const searchTermId = url.searchParams.get("search_term_id")
        expect(searchTermId).toBeTruthy()
        expect(Number(searchTermId)).toBeGreaterThan(0)

        // position doit correspondre à la position dans la liste (1-indexed)
        const position = url.searchParams.get("position")
        expect(position).toBe(String(i + 1))

        // search_term doit être présent et non vide
        const searchTerm = url.searchParams.get("search_term")
        expect(searchTerm).toBeTruthy()
        expect(searchTerm!.length).toBeGreaterThan(0)
        nextUrl = href
      }
    }

    expect(searchTagFound).toBe(true)
    expect(nextUrl).toBeTruthy()
    const response = await page.goto(nextUrl)
    expect(response?.status()).toBe(200)
  })
})
