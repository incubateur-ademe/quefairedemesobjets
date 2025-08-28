import { expect } from "@playwright/test"

const fillAndSelectAutocomplete = async (
  page,
  inputSelector,
  inputText,
  itemSelector,
) => {
  await page.locator(inputSelector).click()
  await page.locator(inputSelector).fill(inputText)
  await expect(page.locator(itemSelector)).toBeInViewport()
  await page.locator(itemSelector).click()
}

export const searchDummySousCategorieObjet = async (page) =>
  await fillAndSelectAutocomplete(
    page,
    "input#id_sous_categorie_objet",
    "chaussures",
    "#id_sous_categorie_objetautocomplete-list.autocomplete-items div:first-of-type",
  )

export const searchDummyAdresse = async (page) =>
  await fillAndSelectAutocomplete(
    page,
    "input#id_adresse",
    "10 rue de la paix",
    "#id_adresseautocomplete-list.autocomplete-items div:nth-of-type(2)",
  )

export const hideDjangoToolbar = async (page) =>
  await page.locator("#djHideToolBarButton").click()

export const getMarkers = async (page) => {
  await expect(page.locator(".maplibregl-marker.home-icon").first()).toBeAttached()
  await page.evaluate(() => {
    document
      .querySelectorAll(".maplibregl-marker.home-icon")
      ?.forEach((element) => element.remove())
  })

  const markers = page?.locator(".maplibregl-marker:has(svg)")

  // Wait for markers to be loaded
  await page.waitForSelector(".maplibregl-marker:has(svg)", {
    state: "attached",
    timeout: 5000,
  })

  // Ensure we have at least one marker, and let's click on a marker.
  // The approach is feels cumbersome, this is because Playwright has a
  // hard time clicking on leaflet markers.
  await expect(markers?.nth(0)).toBeAttached()
  const count = await markers?.count()
  return [markers, count]
}
