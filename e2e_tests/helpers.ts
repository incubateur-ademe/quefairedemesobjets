import { expect } from "@playwright/test"

export async function openAdvancedFilters(
  page,
  parentTestId = "form-content",
  buttonDataTestId = "advanced-filters",
  modalDataTestId = "advanced-filters-modal",
) {
  await page.getByTestId(parentTestId).getByTestId(buttonDataTestId).click()

  await expect(
    page.locator(`[data-testid="${modalDataTestId}"] .fr-modal__content h2`),
  ).toBeInViewport()
  await page
    .locator(`[data-testid="${modalDataTestId}"] .fr-modal__header button`)
    .click()
  await expect(
    page.locator(`[data-testid="${modalDataTestId}"] .fr-modal__content h2`),
  ).toBeHidden()
}

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

export const mockApiAdresse = async (page) =>
  await page.route("https://data.geopf.fr/geocodage/search?q=auray", async (route) => {
    const json = {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-2.990838, 47.668099] },
          properties: {
            label: "Auray",
            score: 0.9476263636363635,
            id: "56007",
            banId: "549cbe54-0b1a-4efd-ae63-fd28ce07ca0d",
            type: "municipality",
            name: "Auray",
            postcode: "56400",
            citycode: "56007",
            x: 250839.06,
            y: 6746792.77,
            population: 14417,
            city: "Auray",
            context: "56, Morbihan, Bretagne",
            importance: 0.42389,
            municipality: "Auray",
            _type: "address",
          },
        },
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-1.581721, 47.262066] },
          properties: {
            label: "Avenue d'Auray 44300 Nantes",
            score: 0.7003545454545453,
            id: "44109_0479",
            banId: "e35da293-0241-49ab-8645-5e520c3b5343",
            name: "Avenue d'Auray",
            postcode: "44300",
            citycode: "44109",
            x: 353734.46,
            y: 6694688.35,
            city: "Nantes",
            context: "44, Loire-Atlantique, Pays de la Loire",
            type: "street",
            importance: 0.7039,
            street: "Avenue d'Auray",
            _type: "address",
          },
        },
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-2.99836, 47.672986] },
          properties: {
            label: "Rue Abbé Philippe le Gall 56400 Auray",
            score: 0.6980245454545453,
            id: "56007_0020",
            banId: "f9cca489-4884-4e1a-9749-c0befb576f4d",
            name: "Rue Abbé Philippe le Gall",
            postcode: "56400",
            citycode: "56007",
            x: 250317.39,
            y: 6747376.96,
            city: "Auray",
            context: "56, Morbihan, Bretagne",
            type: "street",
            importance: 0.67827,
            street: "Rue Abbé Philippe le Gall",
            _type: "address",
          },
        },
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-2.993942, 47.675005] },
          properties: {
            label: "Avenue du Général de Gaulle 56400 Auray",
            score: 0.6979390909090909,
            id: "56007_0420",
            banId: "5cf7532a-0c8b-4aee-aaf6-5bc19e359704",
            name: "Avenue du Général de Gaulle",
            postcode: "56400",
            citycode: "56007",
            x: 250664.97,
            y: 6747575.48,
            city: "Auray",
            context: "56, Morbihan, Bretagne",
            type: "street",
            importance: 0.67733,
            street: "Avenue du Général de Gaulle",
            _type: "address",
          },
        },
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [2.41584, 48.889926] },
          properties: {
            label: "Rue Charles Auray 93500 Pantin",
            score: 0.6972045454545454,
            id: "93055_1440",
            banId: "b761329c-b320-4a1a-90bb-fdcc90197be0",
            name: "Rue Charles Auray",
            postcode: "93500",
            citycode: "93055",
            x: 657165.8,
            y: 6865704.47,
            city: "Pantin",
            context: "93, Seine-Saint-Denis, Île-de-France",
            type: "street",
            importance: 0.66925,
            street: "Rue Charles Auray",
            _type: "address",
          },
        },
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-2.991392, 47.676459] },
          properties: {
            label: "Rue de l’Amiral Coude 56400 Auray",
            score: 0.6957854545454544,
            id: "56007_0040",
            banId: "ee93e999-c3e9-4d8a-a2ae-55ff3c8bb68e",
            name: "Rue de l’Amiral Coude",
            postcode: "56400",
            citycode: "56007",
            x: 250868.01,
            y: 6747722.05,
            city: "Auray",
            context: "56, Morbihan, Bretagne",
            type: "street",
            importance: 0.65364,
            street: "Rue de l’Amiral Coude",
            _type: "address",
          },
        },
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-2.986629, 47.669016] },
          properties: {
            label: "Rue Georges Clemenceau 56400 Auray",
            score: 0.6953527272727272,
            id: "56007_0440",
            banId: "421a4826-9b6c-4c38-8900-fc5d86c6d4c1",
            name: "Rue Georges Clemenceau",
            postcode: "56400",
            citycode: "56007",
            x: 251161.74,
            y: 6746870.42,
            city: "Auray",
            context: "56, Morbihan, Bretagne",
            type: "street",
            importance: 0.64888,
            street: "Rue Georges Clemenceau",
            _type: "address",
          },
        },
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-2.98362, 47.666574] },
          properties: {
            label: "Place de la Republique 56400 Auray",
            score: 0.6947599999999998,
            id: "56007_1210",
            banId: "6c347e14-2449-44e4-98ea-4115d27fa630",
            name: "Place de la Republique",
            postcode: "56400",
            citycode: "56007",
            x: 251366.36,
            y: 6746582.79,
            city: "Auray",
            context: "56, Morbihan, Bretagne",
            type: "street",
            importance: 0.64236,
            street: "Place de la Republique",
            _type: "address",
          },
        },
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-2.979633, 47.667452] },
          properties: {
            label: "Avenue President Wilson 56400 Auray",
            score: 0.694400909090909,
            id: "56007_1160",
            banId: "3c89a749-cbbb-496b-9f4e-1642fdfbffe0",
            name: "Avenue President Wilson",
            postcode: "56400",
            citycode: "56007",
            x: 251672.1,
            y: 6746657.41,
            city: "Auray",
            context: "56, Morbihan, Bretagne",
            type: "street",
            importance: 0.63841,
            street: "Avenue President Wilson",
            _type: "address",
          },
        },
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-2.981106, 47.666589] },
          properties: {
            label: "Rue du Chateau 56400 Auray",
            score: 0.694010909090909,
            id: "56007_0190",
            banId: "15dfa8f2-ed88-44a7-87ab-3495961931b7",
            name: "Rue du Chateau",
            postcode: "56400",
            citycode: "56007",
            x: 251554.62,
            y: 6746570.17,
            city: "Auray",
            context: "56, Morbihan, Bretagne",
            type: "street",
            importance: 0.63412,
            street: "Rue du Chateau",
            _type: "address",
          },
        },
      ],
      query: "auray",
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(json),
    })
  })

export const searchDummySousCategorieObjet = async (page) =>
  await fillAndSelectAutocomplete(
    page,
    "input#id_sous_categorie_objet",
    "chaussures",
    "#id_sous_categorie_objetautocomplete-list.autocomplete-items div:first-of-type",
  )

export const searchDummyAdresse = async (page) => {
  const adresseInput = page.locator('[data-testid="formulaire-adresse-input"]')
  await adresseInput.click()
  await adresseInput.fill("10 rue de la paix")
  const autocompleteOption = page
    .locator(
      ".autocomplete-items div[data-action*='address-autocomplete#selectOption']",
    )
    .nth(1) // Select second option (index 1)
  await expect(autocompleteOption).toBeVisible()
  await autocompleteOption.click()
}

export const getMarkers = async (page) => {
  await expect(page.locator("#pinpoint-home").first()).toBeAttached()
  await page.evaluate(() => {
    document.querySelectorAll("#pinpoint-home")?.forEach((element) => element.remove())
  })

  const markers = await page?.locator(".maplibregl-marker:has(svg)")

  // Ensure we have at least one marker, and let's click on a marker.
  // The approach is feels cumbersome, this is because Playwright has a
  // hard time clicking on leaflet markers.
  await expect(markers?.nth(0)).toBeAttached()
  const count = await markers?.count()
  return [markers, count]
}

export const searchForAuray = async (page) => {
  const adresseInput = page.locator('[data-testid="carte-adresse-input"]')
  await adresseInput.click()
  await adresseInput.fill("Auray")
  const autocompleteOption = page
    .locator(
      ".autocomplete-items div[data-action*='address-autocomplete#selectOption']",
    )
    .first()
  await expect(autocompleteOption).toBeVisible({ timeout: 10000 })
  await autocompleteOption.click()
}

export const searchForAurayInIframe = async (iframe) => {
  const adresseInput = iframe.locator('[data-testid="carte-adresse-input"]')
  await adresseInput.click()
  await adresseInput.fill("Auray")
  const autocompleteOption = iframe
    .locator(
      ".autocomplete-items div[data-action*='address-autocomplete#selectOption']",
    )
    .first()
  await expect(autocompleteOption).toBeVisible({ timeout: 10000 })
  await autocompleteOption.click()
}

export const switchToListeMode = async (page) => {
  const listeButton = page
    .getByTestId("view-mode-nav")
    .getByText("Liste", { exact: true })
  await listeButton.click()

  // Wait for liste mode to be active
  await expect(page.locator('[data-map-target="mapContainer"]')).not.toBeVisible()
}

export const switchToCarteMode = async (page) => {
  const carteButton = page
    .getByTestId("view-mode-nav")
    .getByText("Carte", { exact: true })
  await carteButton.click()

  // Wait for carte mode to be active
  await expect(page.getByTestId("carte-legend")).toBeVisible()
}

export const moveMap = async (page, mapCanvasLocator, offsetX = 100, offsetY = 100) => {
  // Get the bounding box of the canvas to calculate drag coordinates
  await expect(mapCanvasLocator).toBeVisible()
  const canvasBoundingBox = await mapCanvasLocator.boundingBox()
  if (!canvasBoundingBox) {
    throw new Error("Canvas bounding box not found")
  }

  // Drag from center to a new position (simulate panning)
  const centerX = canvasBoundingBox.x + canvasBoundingBox.width / 2
  const centerY = canvasBoundingBox.y + canvasBoundingBox.height / 2

  await page.mouse.move(centerX, centerY)
  await page.mouse.down()
  await page.mouse.move(centerX + offsetX, centerY + offsetY, { steps: 10 })
  await page.mouse.up()
}
