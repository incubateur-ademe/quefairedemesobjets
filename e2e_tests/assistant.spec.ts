import { expect, test } from "@playwright/test"
import { getMarkers, hideDjangoToolbar, mockApiAdresse } from "./helpers"
function getItemSelector(index) {
  return `#mauvais_etat #id_adresseautocomplete-list.autocomplete-items div[data-action="click->address-autocomplete#selectOption"]:nth-of-type(${index})`
}

async function searchOnProduitPage(page, searchedAddress: string) {
  const inputSelector = "#mauvais_etat input#id_adresse"
  await mockApiAdresse(page)

  // Autour de moi
  await page.locator(inputSelector).click()
  await page.locator(inputSelector).pressSequentially(searchedAddress, { delay: 100 })
  await page.locator(getItemSelector(1)).click()
}

test("La carte s'affiche sur une fiche déchet/objet", async ({ page }) => {
  // Navigate to the carte page
  await page.goto(`/dechet/lave-linge`, { waitUntil: "domcontentloaded" })
  await searchOnProduitPage(page, "Auray")
  const sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.adresse).toBe("Auray")
  expect(sessionStorage.latitude).toContain("47.6")
  expect(sessionStorage.longitude).toContain("-2.9")
})

test("Le lien infotri est bien défini", async ({ page }) => {
  // Navigate to the carte page
  await page.goto(`/dechet/lave-linge`, { waitUntil: "domcontentloaded" })
  const href = await page.getByTestId("infotri-link").getAttribute("href")
  expect(href).toBe("https://www.ecologie.gouv.fr/info-tri")
})

test(
  "Les deux recherches en page d'accueil fonctionnent",
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
    await page.goto(`/`, { waitUntil: "domcontentloaded" })

    await page.locator("#id_home-input").click()
    await page.locator("#id_home-input").pressSequentially("lave", { delay: 100 })
    // We expect at least on search result
    await page.waitForResponse(
      (response) =>
        response.url().includes("/assistant/recherche") && response.status() === 200,
    )
    expect(page.locator("main [data-search-target=results] a").first()).toBeAttached()

    await page.locator("#id_header-input").click()
    await page.waitForResponse(
      (response) =>
        response.url().includes("/assistant/recherche") && response.status() === 200,
    )
    expect(page.locator("main [data-search-target=results] a")).toHaveCount(0)
    await page.locator("#id_header-input").pressSequentially("lave")
    await page.waitForResponse(
      (response) =>
        response.url().includes("/assistant/recherche") && response.status() === 200,
    )
    expect(page.locator("main [data-search-target=results] a")).toHaveCount(0)
    expect(
      page.locator("#header [data-search-target=results] a").first(),
    ).toBeAttached()

    await page.locator("#id_home-input").click()
    await page.waitForResponse(
      (response) =>
        response.url().includes("/assistant/recherche") && response.status() === 200,
    )
    expect(page.locator("#home [data-search-target=results] a")).toHaveCount(0)
    expect(page.locator("#header [data-search-target=results] a")).toHaveCount(0)
  },
)

test("Le tracking PostHog fonctionne comme prévu", async ({ page }) => {
  // Check that homepage scores 1
  await page.goto(`/`, { waitUntil: "domcontentloaded" })
  let sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.homePageView).toBe("0")

  // Navigate to a produit page and check that it scores 1
  await page.goto(`/dechet/lave-linge`, { waitUntil: "domcontentloaded" })
  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.produitPageView).toBe("1")

  // Click on a pin on the map and check that it scores 1
  await searchOnProduitPage(page, "Auray")
  const [markers, count] = await getMarkers(page)
  for (let i = 0; i < count; i++) {
    const item = markers?.nth(i)

    try {
      await item!.click({ force: true })
      break
    } catch (e) {
      console.log("cannot click", e)
    }
  }

  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.userInteractionWithMap).toBe("1")

  // Click on another pin on the map and check that it scores 1 more (2 in total)
  for (let i = 0; i < count; i++) {
    const item = markers?.nth(i)

    try {
      await item!.click({ force: true })
      break
    } catch (e) {
      console.log("cannot click", e)
    }
  }

  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.userInteractionWithMap).toBe("2")

  // Click on share button in solution details
  await page
    .locator("#mauvais_etat [aria-describedby='mauvais_etat:shareTooltip']")
    .click()
  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.userInteractionWithSolutionDetails).toBe("1")

  // Ensure that the scores does not increases after
  // several homepage visits
  await page.goto(`/`, { waitUntil: "domcontentloaded" })
  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.homePageView).toBe("0")
})
