import { expect } from "@playwright/test"
import { test } from "./fixtures"
import {
  mockApiAdresse,
  navigateTo,
  searchForAuray,
  TIMEOUT,
} from "./helpers"

test.describe("🗺️ GeoJSON acteur layer (post-migration flow)", () => {
  test(
    "Searching a municipality fetches /carte/acteurs.geojson and renders markers",
    async ({ page }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)

      const geojsonResponsePromise = page.waitForResponse(
        (r) =>
          r.url().includes("/carte/acteurs.geojson") &&
          r.status() === 200,
        { timeout: TIMEOUT.LONG },
      )

      await searchForAuray(page)
      const geojsonResponse = await geojsonResponsePromise

      const url = new URL(geojsonResponse.url())
      expect(url.searchParams.get("bbox")).toBeTruthy()
      expect(url.searchParams.get("zoom")).toBeTruthy()

      const payload = await geojsonResponse.json()
      expect(payload.type).toBe("FeatureCollection")
      expect(Array.isArray(payload.features)).toBe(true)
      expect(typeof payload.truncated).toBe("boolean")
    },
  )

  test(
    "Municipality search fetches the commune polygon proxy and persists the citycode in sessionStorage",
    async ({ page }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)

      // Auray's INSEE citycode is 56007 (see mockApiAdresse fixture).
      const polygonPromise = page.waitForResponse(
        (r) =>
          r.url().includes("/carte/communes/56007") && r.status() === 200,
        { timeout: TIMEOUT.LONG },
      )

      await searchForAuray(page)
      await polygonPromise

      const citycode = await page.evaluate(() =>
        sessionStorage.getItem("citycode"),
      )
      expect(citycode).toBe("56007")

      const hiddenInputValue = await page
        .locator('input[name$="-search_area_citycode"]')
        .first()
        .inputValue()
      expect(hiddenInputValue).toBe("56007")
    },
  )

  test(
    "Reload after a municipality search restores the citycode hidden input from sessionStorage",
    async ({ page }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)
      await searchForAuray(page)

      // Confirm citycode landed in sessionStorage as a precondition.
      await expect
        .poll(async () => page.evaluate(() => sessionStorage.getItem("citycode")))
        .toBe("56007")

      // Full reload: wipes JS state but sessionStorage survives.
      await page.reload()

      // The hidden form field should rehydrate from sessionStorage by the
      // assistant `state` controller's `updateUIFromGlobalState`.
      await expect(
        page.locator('input[name$="-search_area_citycode"]').first(),
      ).toHaveValue("56007", { timeout: TIMEOUT.LONG })
    },
  )

  test(
    "Picking a non-municipality address fires the KNN endpoint instead of the bbox one",
    async ({ page }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)

      // Listen for the KNN call BEFORE clicking the autocomplete option, so
      // we don't race the post-Turbo-swap fetch. The street-typed BAN result
      // routes through /carte/acteurs-near.geojson (KNN), not the bbox one.
      const knnPromise = page.waitForResponse(
        (r) =>
          r.url().includes("/carte/acteurs-near.geojson") &&
          r.status() === 200,
        { timeout: TIMEOUT.LONG },
      )

      // Type a fragment that surfaces street-typed suggestions, then pick the
      // "Avenue d'Auray … Nantes" entry (type=street in the mock).
      const inputLocator = page.locator('[data-testid="carte-adresse-input"]')
      await inputLocator.click()
      await inputLocator.clear()
      await inputLocator.pressSequentially("Auray", { delay: 30 })

      const streetOption = page
        .locator(
          ".autocomplete-items div[data-action*='address-autocomplete#selectOption']",
        )
        .filter({ hasText: "Avenue d'Auray" })
        .first()
      await expect(streetOption).toBeVisible({ timeout: TIMEOUT.DEFAULT })
      await streetOption.click()

      const knnResponse = await knnPromise
      const knnUrl = new URL(knnResponse.url())
      expect(knnUrl.searchParams.get("lat")).toBeTruthy()
      expect(knnUrl.searchParams.get("lng")).toBeTruthy()
    },
  )

  test(
    "Cap and truncated flag are honored by the bbox endpoint",
    async ({ page }) => {
      await navigateTo(page, "/carte")

      // Hit the endpoint directly with a wide France-wide bbox at a high zoom
      // to force the 200-feature cap + truncation flag.
      const r = await page.request.get(
        "/carte/acteurs.geojson?bbox=-5.5,41.0,9.5,51.5&zoom=13",
      )
      expect(r.status()).toBe(200)
      const payload = await r.json()
      expect(payload.features.length).toBeLessThanOrEqual(200)
      // At France-wide zoom 13 there are vastly more than 200 acteurs, so the
      // response should advertise truncation.
      expect(payload.truncated).toBe(true)
    },
  )
})
