import { expect, test } from "@playwright/test"
import {
  AURAY,
  MONTBELIARD,
  chooseSuggestion,
  dragAssistantMap,
  mockAssistantAddressServices,
  navigateTo,
  pinpointUuids,
  waitForLieux,
} from "./helpers"

test.use({ geolocation: AURAY, permissions: ["geolocation"] })

test.describe("🧭 Parcours de l'assistant", () => {
  test("De la recherche au lieu, par géolocalisation puis par adresse", async ({
    page,
  }) => {
    await mockAssistantAddressServices(page)
    let auray: string[] = []

    await test.step("Recherche d'un objet sans adresse", async () => {
      await navigateTo(page, "/assistant/")
      await chooseSuggestion(page, "recherche-objet", "vélo", "Vélo")
      await page.getByRole("button", { name: "Lancer la recherche" }).click()
      await expect(page).toHaveURL(/\/assistant\/objet\/velo\//)
    })

    await test.step("La géolocalisation ouvre les lieux autour de moi", async () => {
      const reverse = page.waitForRequest(/\/qfdmo\/autocomplete\/reverse\?/)
      const lieux = waitForLieux(page, (url) =>
        url.includes(`latitude=${AURAY.latitude}`),
      )
      await page
        .getByRole("link", { name: "Je découvre les solutions près de moi" })
        .first()
        .click()
      await reverse
      await expect(page).toHaveURL(/\/assistant\/solutions\/.*precise=true/)
      await expect(page.locator("#recherche-adresse-champ")).toHaveValue("Auray")
      expect((await lieux).length).toBeGreaterThan(0)
      auray = await pinpointUuids(page)
    })

    await test.step("La carte se déplace et garde ses lieux", async () => {
      const explored = waitForLieux(page, (url) => url.includes("bbox="))
      await dragAssistantMap(page, 40, 40)
      await explored
      const kept = await pinpointUuids(page)
      expect(auray.filter((uuid) => kept.includes(uuid)).length).toBeGreaterThan(0)
    })

    await test.step("Un lieu, puis retour aux mêmes solutions", async () => {
      await page.evaluate(
        () => ((window as { sameDocument?: boolean }).sameDocument = true),
      )
      const [uuid] = auray
      // Out of the viewport after the drag: a click on its link, not on screen.
      await page.locator(`.qfa-pinpoint[data-uuid="${uuid}"]`).dispatchEvent("click")
      await expect(page).toHaveURL(new RegExp(`/assistant/lieu/${uuid}/`))
      await expect(page.locator("h1")).toBeVisible()

      await page.goBack()
      await expect(page).toHaveURL(/\/assistant\/solutions\//)
      expect(await pinpointUuids(page)).toContain(uuid)
      // Turbo Drive: the whole journey stays in one document.
      expect(
        await page.evaluate(() => (window as { sameDocument?: boolean }).sameDocument),
      ).toBe(true)

      await page.goBack()
      await expect(page).toHaveURL(/\/assistant\/objet\/velo\//)
      await expect(page.locator("#recherche-objet-champ")).toHaveValue("Vélo")
    })

    await test.step("Une nouvelle adresse charge d'autres lieux", async () => {
      await chooseSuggestion(page, "recherche-adresse", "Montbéliard", "Montbéliard")
      await expect(page).toHaveURL(/adresse=Montb/)
      const lieux = waitForLieux(page, (url) =>
        url.includes(`latitude=${MONTBELIARD.latitude}`),
      )
      await page
        .getByRole("link", { name: "Je découvre les solutions", exact: true })
        .first()
        .click()
      const montbeliard = await lieux
      expect(montbeliard.filter((uuid) => auray.includes(uuid))).toEqual([])
      await expect
        .poll(async () =>
          (await pinpointUuids(page)).some((uuid) => auray.includes(uuid)),
        )
        .toBe(false)
      expect(await pinpointUuids(page)).toContain(montbeliard[0])
      await expect(page.locator(".qfa-pinpoint--address")).toHaveCount(0)
    })
  })
})
