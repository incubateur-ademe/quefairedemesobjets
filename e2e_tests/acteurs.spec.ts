import { expect, test } from "@playwright/test";
import { hideDjangoToolbar, searchDummyAdresse } from "./helpers";
function getItemSelector(index) {
  return `#mauvais_etat #id_adresseautocomplete-list.autocomplete-items div:nth-of-type(${index})`
}


test("Desktop | Les acteurs sont visibles sur la carte du formulaire fonctionne", async ({ page }) => {
  // Navigate to the carte page
  await page.goto(`/test_iframe`, { waitUntil: "networkidle" });
  // await hideDjangoToolbar(page)
  const sessionStorage = await page.evaluate(() => window.sessionStorage)
  const iframeElement = await page.$("#formulaire iframe");
  const iframe = await iframeElement?.contentFrame();

  // Select a Produit
  let inputSelector = "#id_sous_categorie_objet"
  await iframe.locator(inputSelector).click()
  await iframe.locator(inputSelector).fill("perceuse");
  await iframe.locator("#id_sous_categorie_objetautocomplete-list.autocomplete-items div:nth-child(1)").click()

  // Fill adresse
  inputSelector = "#id_adresse"
  await iframe.locator(inputSelector).click()
  await iframe.locator(inputSelector).fill("auray");
  await iframe.locator("#id_adresseautocomplete-list.autocomplete-items div:nth-child(2)").click()

  // Submit form
  await iframe?.getByTestId("formulaire-rechercher-adresses-submit").click()
  const markers = iframe?.locator(".leaflet-marker-icon")

  // Remove the home marker (red dot) that prevents Playwright from clicking other markers
  await page.evaluate(() => {
    const element = document.querySelector('.leaflet-marker-icon');
    if (element) {
      element.remove();
    }
  });

  // Ensure we have at least one marker, and let's click on a marker.
  // The approach is feels cumbersome, this is because Playwright has a
  // hard time clicking on leaflet markers.
  // Hence the force option in click's method call.
  await expect(markers?.nth(0)).toBeAttached()
  const count = await markers?.count() || 0
  for (let i = 0; i < count; i++) {
    const item = markers?.nth(i);

    try {
      await item!.click({ force: true, timeout: 100 });
      break
    } catch (e) {
      console.log("cannot click", e)
    }
  }

  await expect(iframe?.locator("#acteurDetailsPanel")).toBeVisible()
})

test("Desktop | Les acteurs digitaux sont visibles sur le formulaire", async ({ page }) => {
  test.slow()
  // Navigate to the carte page
  await page.goto(`/test_iframe`, { waitUntil: "networkidle" });
  // await hideDjangoToolbar(page)
  const sessionStorage = await page.evaluate(() => window.sessionStorage)
  const iframeElement = await page.$("#formulaire iframe");
  const iframe = await iframeElement?.contentFrame();

  // Select a Produit
  let inputSelector = "#id_sous_categorie_objet"
  await iframe.locator(inputSelector).click()
  await iframe.locator(inputSelector).fill("perceuse");
  await iframe.locator("#id_sous_categorie_objetautocomplete-list.autocomplete-items div:nth-child(1)").click()

  // Fill adresse
  inputSelector = "#id_adresse"
  await iframe.locator(inputSelector).click()
  await iframe.locator(inputSelector).fill("auray");
  await iframe.locator("#id_adresseautocomplete-list.autocomplete-items div:nth-child(2)").click()

  // Submit form
  await iframe?.getByTestId("formulaire-rechercher-adresses-submit").click()
  // Wait for results to laod en being added to leaflet
  const someLeafletMarker = iframe?.locator(".leaflet-marker-icon").first()
  await expect(someLeafletMarker).toBeAttached()

  // Digital acteurs
  await iframe?.locator("#id_digital_1").click({ force: true })
  await iframe?.getByTestId("[aria-controls=acteurDetailsPanel]").first().click()
  await expect(iframe?.locator("#acteurDetailsPanel")).toBeVisible()
})

