import { expect, test } from "@playwright/test"
import {
  AURAY,
  getIframe,
  mockAssistantAddressServices,
  pinpointUuids,
  waitForIframeResize,
} from "./helpers"

// A reuser's page: another origin than the iframe (`localhost`).
const HOST_PAGE =
  "http://127.0.0.1:8888/lookbook/preview/tests/t_20_assistant_v2_redirect/?objet=velo"

test.use({ geolocation: AURAY, permissions: ["geolocation"] })

test.describe("🪟 Assistant intégré chez un réutilisateur", () => {
  test("Le script ouvre la fiche, et le parcours reste dans l'iframe", async ({
    page,
  }) => {
    await mockAssistantAddressServices(page)
    const iframe = getIframe(page, "assistant")

    await test.step("Le script ouvre la fiche de l'objet", async () => {
      await page.goto(HOST_PAGE)
      await expect(iframe.locator("#recherche-objet-champ")).toHaveValue("Vélo")
      await waitForIframeResize(page, "assistant")
    })

    await test.step("La géolocalisation fonctionne dans l'iframe", async () => {
      await iframe
        .getByRole("link", { name: "Je découvre les solutions près de moi" })
        .first()
        .click()
      await expect(iframe.locator("#recherche-adresse-champ")).toHaveValue("Auray")
      expect((await pinpointUuids(iframe)).length).toBeGreaterThan(0)
      expect(page.url()).toBe(HOST_PAGE)
    })

    await test.step("Le retour du navigateur ramène l'iframe à la fiche", async () => {
      // Only the iframe navigates back: page.goBack() would wait for the page.
      await page.evaluate(() => history.back())
      await expect(iframe.locator("#recherche-objet-champ")).toHaveValue("Vélo")
      await expect(iframe.locator("#recherche-adresse-champ")).toHaveValue("")
      expect(page.url()).toBe(HOST_PAGE)
    })
  })
})
