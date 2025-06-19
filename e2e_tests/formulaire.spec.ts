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

test("Desktop | Le parcours carte du formulaire fonctionne", async ({ page }) => {
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

  // Submit
  await iframe?.getByTestId("rechercher-adresses-submit").click()
  await expect(iframe.locator(".leaflet-marker-icon")).toBeVisible()

  // Digital acteurs
  await iframe.locator("#id_digital_1").click()
  await expect(iframe?.getByTestId("digital-acteurs-results")!).toBeVisible()
})

