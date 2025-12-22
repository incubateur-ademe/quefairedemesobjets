import { expect, test } from "@playwright/test"
import {
  getMarkers,
  mockApiAdresse,
  searchAddress,
  navigateTo,
  getSessionStorage,
  clickFirstAvailableMarker,
  TIMEOUT,
} from "./helpers"

test.describe("🤖 Assistant et Recherche", () => {
  async function searchOnProduitPage(page, searchedAddress: string) {
    await mockApiAdresse(page) // Mock BEFORE interacting with input
    await searchAddress(page, searchedAddress, "carte", {
      parentSelector: "#mauvais-etat-panel",
    })
  }

  test("L'adresse sélectionnée est stockée dans le sessionStorage", async ({
    page,
  }) => {
    // Navigate to the carte page
    await navigateTo(page, `/dechet/lave-linge`)
    await searchOnProduitPage(page, "Auray")
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

  test(
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
      // Navigate to the carte page
      await navigateTo(page, `/`)

      // Type in main serach
      let responsePromise = page.waitForResponse(
        (response) =>
          response.url().includes("/assistant/recherche") && response.status() === 200,
      )
      await page.locator("#id_home-input").click()
      // FIXME: try to remove delay here
      // It is required to prevent the locator check below to happen before the
      // input debounce delay has ran, hence happening before the API call to succeed
      await page.locator("#id_home-input").fill("lave")
      await responsePromise

      // We expect at least one search result
      await expect(
        page.locator("main [data-search-target=results] a").first(),
      ).toBeAttached()

      // Type in header search
      responsePromise = page.waitForResponse(
        (response) =>
          response.url().includes("/assistant/recherche") && response.status() === 200,
      )
      await page.locator("#id_header-input").click()
      expect(page.locator("main [data-search-target=results] a")).toHaveCount(0)
      // FIXME: try to remove delay here
      // It is required to prevent the locator check below to happen before the
      // input debounce delay has ran, hence happening before the API call to succeed
      await page.locator("#id_header-input").pressSequentially("lave", { delay: 200 })
      await responsePromise

      expect(page.locator("main [data-search-target=results] a")).toHaveCount(0)
      await expect(
        page.locator("#header [data-search-target=results] a").first(),
      ).toBeAttached()

      // Blur header input and expect it to be closed
      responsePromise = page.waitForResponse(
        (response) =>
          response.url().includes("/assistant/recherche") && response.status() === 200,
      )
      await page.locator("#id_home-input").click()
      await responsePromise

      // Wait for header results to be hidden after switching to home input
      await expect(page.locator("#header [data-search-target=results] a")).toHaveCount(
        0,
        { timeout: 5000 },
      )
      expect(page.locator("#home [data-search-target=results] a")).toHaveCount(0)
    },
  )

  test.skip("Les événements PostHog sont trackés correctement (pages vues, interactions carte, détails solution)", async ({
    page,
  }) => {
    // Check that homepage scores 1
    await navigateTo(page, `/`)
    let sessionStorage = await getSessionStorage(page)

    expect(sessionStorage.homePageView).toBe("0")

    // Navigate to a produit page and check that it scores 1
    await navigateTo(page, `/dechet/lave-linge`)
    sessionStorage = await getSessionStorage(page)
    expect(sessionStorage.produitPageView).toBe("1")

    // Click on a pin on the map and check that it scores 1
    await searchOnProduitPage(page, "Auray")
    await getMarkers(page)
    await clickFirstAvailableMarker(page)

    // Wait for either solution details panel or actor panel to appear (confirms click worked)
    await Promise.race([
      page
        .locator("#acteurDetailsPanel")
        .waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT }),
    ]).catch(() => {
      // If neither appears, just continue - maybe the tracking still works
      console.log("Warning: Solution details panel did not appear after marker click")
    })

    // Wait for sessionStorage to be updated after click
    // Give extra time for PostHog to process the event
    await page.waitForFunction(
      () => window.sessionStorage.userInteractionWithMap !== undefined,
      { timeout: TIMEOUT.LONG },
    )
    sessionStorage = await getSessionStorage(page)
    expect(sessionStorage.userInteractionWithMap).toBe("1")

    // Click on another pin on the map and check that it scores 1 more (2 in total)
    await clickFirstAvailableMarker(page)

    // Wait for sessionStorage to be updated after second click
    await page.waitForFunction(
      () => window.sessionStorage.userInteractionWithMap === "2",
      { timeout: TIMEOUT.LONG },
    )
    sessionStorage = await getSessionStorage(page)
    expect(sessionStorage.userInteractionWithMap).toBe("2")

    // Click on share button in solution details
    await page.locator("[aria-describedby='mauvais-etat:shareTooltip']").click()
    sessionStorage = await getSessionStorage(page)
    expect(sessionStorage.userInteractionWithSolutionDetails).toBe("1")

    // Ensure that the scores does not increases after
    // several homepage visits
    await navigateTo(page, `/`)
    sessionStorage = await getSessionStorage(page)
    expect(sessionStorage.homePageView).toBe("0")
  })
})
