import { expect, test } from "@playwright/test";
import { hideDjangoToolbar, searchDummyAdresse } from "./helpers";
function getItemSelector(index) {
  return `#mauvais_etat #id_adresseautocomplete-list.autocomplete-items div:nth-of-type(${index})`
}

async function searchOnProduitPage(page, searchedAddress: string) {
  const inputSelector = "#mauvais_etat input#id_adresse"

  // Autour de moi
  await page.locator(inputSelector).click();
  await page.locator(inputSelector).fill(searchedAddress);
  expect(page.locator(getItemSelector(1)).innerText()).not.toBe("Autour de moi")
  await page.locator(getItemSelector(1)).click();
}

test("Desktop | La carte s'affiche sur une fiche déchet/objet", async ({ page }) => {
  // Navigate to the carte page
  await page.goto(`/dechet/lave-linge`, { waitUntil: "networkidle" });
  await hideDjangoToolbar(page)
  const sessionStorage = await page.evaluate(() => window.sessionStorage)
  await searchOnProduitPage(page, "Auray")
  expect(sessionStorage.adresse).toBe("Auray")
  expect(sessionStorage.latitude).toContain("47.6")
  expect(sessionStorage.longitude).toContain("-2.9")
})

test("Desktop | Le tracking PostHog fonctionne comme prévu", async ({ page }) => {
  // Check that homepage scores 1
  await page.goto(`/`, { waitUntil: "networkidle" });
  await hideDjangoToolbar(page)
  let sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.homePageView).toBe("1")

  // Navigate to a produit page and check that it scores 1
  await page.goto(`/dechet/lave-linge`, { waitUntil: "networkidle" });
  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.produitPageView).toBe("1")

  // Click on a pin on the map and check that it scores 1
  // await searchOnProduitPage(page, "Auray")
  // await page.locator("#mauvais_etat .leaflet-marker-icon:nth-child(3)").click()
  // sessionStorage = await page.evaluate(() => window.sessionStorage)
  // console.log({ sessionStorage })
  // expect(sessionStorage.userInteractionWithMap).toBe("1")

  // Click on another pin on the map and check that it scores 1 more (2 in total)
  // await page.locator("#mauvais_etat .leaflet-marker-icon:nth-child(4)").click({ force: true})
  // sessionStorage = await page.evaluate(() => window.sessionStorage)
  // expect(sessionStorage.userInteractionWithMap).toBe("2")

  // Click on another pin on the map and check that it scores 1 more (2 in total)
  // await page.locator("#mauvais_etat .leaflet-marker-icon:nth-child(5)").click({ force: true})
  // sessionStorage = await page.evaluate(() => window.sessionStorage)
  // expect(sessionStorage.userInteractionWithMap).toBe("2")

  // Click on another pin on the map and check that it scores 1 more (2 in total)
  // await page.locator("#mauvais_etat [aria-describedby=mauvais_etat:shareTooltip]").click()
  // sessionStorage = await page.evaluate(() => window.sessionStorage)
  // expect(sessionStorage.userInteractionWithSolutionDetails).toBe("1")

  // Ensure that the scores does not increases after
  // several homepage visits
  await page.goto(`/`, { waitUntil: "networkidle" });
  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.homePageView).toBe("1")
})
