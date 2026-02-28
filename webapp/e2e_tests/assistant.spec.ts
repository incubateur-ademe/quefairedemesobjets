import { expect, test } from "@playwright/test"
import {
  navigateTo,
  getSessionStorage,
  clickFirstClickableActeurMarker,
  TIMEOUT,
  searchOnProduitPage as searchOnProduitPage,
} from "./helpers"

test.describe("🤖 Assistant et Recherche", () => {
  test("L'adresse sélectionnée est stockée dans le sessionStorage", async ({
    page,
  }) => {
    // Navigate to the carte page
    await navigateTo(page, `/dechet/lave-linge`)
    await searchOnProduitPage(page, "Auray")

    // Wait for sessionStorage to be updated after selecting the address
    // The address selection triggers an event chain: autocomplete -> state controller -> sessionStorage
    await page.waitForFunction(
      () => window.sessionStorage.getItem("adresse") === "Auray",
      { timeout: TIMEOUT.DEFAULT },
    )

    const sessionStorage = await getSessionStorage(page)
    expect(sessionStorage.adresse).toBe("Auray")
    expect(sessionStorage.latitude).toContain("47.6")
    expect(sessionStorage.longitude).toContain("-2.9")
  })

  test("Le lien infotri pointe vers le bon URL", async ({ page }) => {
    // Navigate to the carte page
    await navigateTo(page, `/dechet/lave-linge`)
    const href = await page.getByTestId("infotri-link").getAttribute("href")
    expect(href).toBe("https://www.ecologie.gouv.fr/info-tri")
  })

  // The UI is changing for this test.
  // It will be rewritten once DSFR in header search will be merged, alongside the homepage revamp
  // that introduces a new search design.
  test.skip(
    "Les champs de recherche en page d'accueil (principal et header) fonctionnent indépendamment",
    {
      annotation: [
        {
          type: "issue",
          description:
            "https://www.notion.so/accelerateur-transition-ecologique-ademe/Assistant-Probl-me-sur-la-double-recherche-en-page-d-accueil-22a6523d57d78057981df59c74704cf9?source=copy_link",
        },
      ],
    },
    async ({ page }) => {
      // Navigate to the homepage
      await navigateTo(page, `/`)

      // Type in main search (uses /assistant/recherche endpoint)
      let responsePromise = page.waitForResponse(
        (response) =>
          response.url().includes("/assistant/recherche") && response.status() === 200,
      )
      await page.locator("#id_home-input").click()
      await page.locator("#id_home-input").fill("lave")
      await responsePromise

      // We expect at least one search result in the home search
      await expect(
        page.locator("main [data-search-target=results] a").first(),
      ).toBeAttached()

      // Click on header search - this triggers autocomplete-search due to showOnFocus
      responsePromise = page.waitForResponse(
        (response) =>
          response.url().includes("/assistant/autocomplete-search") &&
          response.status() === 200,
      )
      await page.locator("#id_header-autocomplete-search").click()
      await responsePromise

      // Main search results should be cleared when clicking header search
      await expect(page.locator("main [data-search-target=results] a")).toHaveCount(0)

      // Type in header search
      responsePromise = page.waitForResponse(
        (response) =>
          response.url().includes("/assistant/autocomplete-search") &&
          response.status() === 200,
      )
      await page
        .locator("#id_header-autocomplete-search")
        .pressSequentially("lave", { delay: 200 })
      await responsePromise

      // Main search results should still be empty (header search is independent)
      await expect(page.locator("main [data-search-target=results] a")).toHaveCount(0)

      // Click back on home input - header autocomplete should close (clickOutside)
      await page.locator("#id_home-input").click()

      // Wait for header results to be hidden after switching to home input
      await expect(
        page.locator("#modal-search [data-next-autocomplete-target=results]"),
      ).toBeHidden({ timeout: 5000 })

      // Home search results should be empty since we clicked (cleared the search)
      await expect(page.locator("main [data-search-target=results] a")).toHaveCount(0)
    },
  )

  test("Les événements PostHog sont trackés correctement (pages vues, interactions carte, détails solution)", async ({
    page,
  }) => {
    test.slow()
    // Check that homepage scores 1
    await navigateTo(page, `/`)
    let sessionStorage = await getSessionStorage(page)

    expect(sessionStorage.homePageView).toBe("0")

    // Navigate to a produit page and check that it scores 1
    await navigateTo(page, `/categories/meubles/`)
    sessionStorage = await getSessionStorage(page, "produitPageView")
    expect(sessionStorage.produitPageView).toBe("1")

    // Click on a pin on the map and check that it scores 1
    await searchOnProduitPage(page, "Auray")
    await clickFirstClickableActeurMarker(page)

    page
      .locator("#acteurDetailsPanel")
      .waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })

    sessionStorage = await getSessionStorage(page, "userInteractionWithMap")
    expect(sessionStorage.userInteractionWithMap).toBe("1")

    // Click on another pin on the map and check that it scores 1 more (2 in total)
    await clickFirstClickableActeurMarker(page)

    sessionStorage = await getSessionStorage(page, "userInteractionWithMap")
    expect(sessionStorage.userInteractionWithMap).toBe("2")

    // Click on share button in solution details
    const boutonItineraire = page.getByText("Itinéraire")
    const itineraireLink = page.locator("a").filter({ has: boutonItineraire })
    await itineraireLink.click()
    sessionStorage = await getSessionStorage(page, "userInteractionWithSolutionDetails")
    expect(sessionStorage.userInteractionWithSolutionDetails).toBe("1")

    // Ensure that the scores does not increases after
    // several homepage visits
    await navigateTo(page, `/`)
    sessionStorage = await getSessionStorage(page, "homePageView")
    expect(sessionStorage.homePageView).toBe("0")
  })
})
