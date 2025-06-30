import { expect, test } from "@playwright/test"
import { hideDjangoToolbar, searchDummyAdresse } from "./helpers"
function getItemSelector(index) {
  return `#mauvais_etat #id_adresseautocomplete-list.autocomplete-items div:nth-of-type(${index})`
}

async function searchOnProduitPage(page, searchedAddress: string) {
  const inputSelector = "#mauvais_etat input#id_adresse"

  // Autour de moi
  await page.locator(inputSelector).click()
  await page.locator(inputSelector).fill(searchedAddress)
  expect(page.locator(getItemSelector(1)).innerText()).not.toBe("Autour de moi")
  await page.locator(getItemSelector(1)).click()
}

test("Desktop | La carte s'affiche sur une fiche déchet/objet", async ({ page }) => {
  // Navigate to the carte page
  await page.goto(`/dechet/lave-linge`, { waitUntil: "networkidle" })
  // await hideDjangoToolbar(page)
  await searchOnProduitPage(page, "Auray")
  const sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.adresse).toBe("Auray")
  expect(sessionStorage.latitude).toContain("47.6")
  expect(sessionStorage.longitude).toContain("-2.9")
})

test("Desktop | Le tracking PostHog fonctionne comme prévu", async ({ page }) => {
  // Check that homepage scores 1
  await page.goto(`/`, { waitUntil: "networkidle" })
  // await hideDjangoToolbar(page)
  let sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.homePageView).toBe("0")

  // Navigate to a produit page and check that it scores 1
  await page.goto(`/dechet/lave-linge`, { waitUntil: "networkidle" })
  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.produitPageView).toBe("1")

  // Click on a pin on the map and check that it scores 1
  await searchOnProduitPage(page, "Auray")
  const markers = page.locator(".leaflet-marker-icon")
  // Remove the home marker (red dot) that prevents Playwright from clicking other markers
  await page.evaluate(() => {
    document.querySelector(".leaflet-marker-icon.home-icon")?.remove()
  })

  // Ensure we have at least one marker, and let's click on a marker.
  // The approach is feels cumbersome, this is because Playwright has a
  // hard time clicking on leaflet markers.
  // Hence the force option in click's method call.
  await expect(markers?.nth(0)).toBeAttached()
  const count = await markers?.count()
  for (let i = 0; i < count; i++) {
    const item = markers?.nth(i)

    try {
      await item!.click({ force: true, timeout: 100 })
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
      await item!.click({ force: true, timeout: 100 })
      break
    } catch (e) {
      console.log("cannot click", e)
    }
  }

  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.userInteractionWithMap).toBe("2")

  // Click on share button in solution details
  await page
<<<<<<< HEAD
    .locator("#mauvais_etat [aria-describedby='mauvais_etat:shareTooltip']")
=======
    .locator("#mauvais_etat [aria-describedby=mauvais_etat:shareTooltip]")
>>>>>>> c926dbea (Fix fixtures installation)
    .click()
  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.userInteractionWithSolutionDetails).toBe("1")

  // Ensure that the scores does not increases after
  // several homepage visits
  await page.goto(`/`, { waitUntil: "networkidle" })
  sessionStorage = await page.evaluate(() => window.sessionStorage)
  expect(sessionStorage.homePageView).toBe("0")
})
