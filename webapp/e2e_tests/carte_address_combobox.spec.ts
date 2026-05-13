import { expect, Page } from "@playwright/test"
import { test } from "./fixtures"
import { mockCarteAutocompleteAddress, navigateTo, TIMEOUT } from "./helpers"

/**
 * Covers the next-autocomplete carte combobox:
 *
 *   1. typing fires a Turbo Frame fetch and renders BAN suggestions
 *   2. picking a suggestion populates lat/lng, dispatches change, submits form
 *   3. reloading after a pick does NOT enter a resubmit loop
 *   4. the form serializes exactly one `adresse` field (regression: the
 *      visible search input used to share its `name` with a hidden sibling,
 *      sending `adresse=""` and triggering the loop above)
 */

const CARTE_INPUT = '[data-testid="carte-adresse-input"]'
const CARTE_OPTION = '[role="option"][data-next-autocomplete-target="option"]'
const ADRESSE_FIELD_NAME = "carte_map-adresse"

/**
 * Type a query into the carte combobox and click the first matching suggestion.
 * Waits for the Turbo Frame response to settle before clicking.
 */
async function pickFirstAddress(page: Page, query: string): Promise<void> {
  const input = page.locator(CARTE_INPUT)
  await input.click()
  await input.fill(query)

  // Wait for our mocked Turbo Frame response before reaching for the option.
  await page.waitForResponse(
    (response) =>
      response.url().includes("/qfdmo/autocomplete/address") &&
      response.url().includes(`q=${query}`) &&
      response.status() === 200,
    { timeout: TIMEOUT.DEFAULT },
  )

  const firstOption = page.locator(CARTE_OPTION).filter({ hasText: query }).first()
  await expect(firstOption).toBeVisible({ timeout: TIMEOUT.DEFAULT })
  await firstOption.click()
}

test.describe("🗺️ Carte address combobox", () => {
  test.beforeEach(async ({ page }) => {
    // Always intercept the Turbo Frame autocomplete endpoint with deterministic
    // results so the test never depends on data.geopf.fr being available.
    await mockCarteAutocompleteAddress(page)
  })

  test("typing renders BAN suggestions with role=option", async ({ page }) => {
    await navigateTo(page, "/carte")
    await page.locator(CARTE_INPUT).fill("Auray")

    const options = page.locator(CARTE_OPTION)
    await expect(options.first()).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    await expect(options.first()).toHaveText(/Auray/)
    await expect(options.first()).toHaveAttribute("data-lat", "47.668099")
    await expect(options.first()).toHaveAttribute("data-lon", "-2.990838")
  })

  test("picking a suggestion populates lat/lng and submits the form", async ({
    page,
  }) => {
    await navigateTo(page, "/carte")
    await pickFirstAddress(page, "Auray")

    // Selected label lands in the visible input.
    await expect(page.locator(CARTE_INPUT)).toHaveValue("Auray")

    // The carte controller wrote the coordinates onto the hidden fields.
    const latitude = page.locator('[data-carte-address-autocomplete-target="latitude"]')
    const longitude = page.locator(
      '[data-carte-address-autocomplete-target="longitude"]',
    )
    await expect(latitude).toHaveValue("47.668099")
    await expect(longitude).toHaveValue("-2.990838")

    // state.ts mirrors the chosen location into sessionStorage.
    const persisted = await page.evaluate(() => ({
      adresse: sessionStorage.getItem("adresse"),
      latitude: sessionStorage.getItem("latitude"),
      longitude: sessionStorage.getItem("longitude"),
    }))
    expect(persisted).toEqual({
      adresse: "Auray",
      latitude: "47.668099",
      longitude: "-2.990838",
    })
  })

  test("the address field is serialized exactly once when the form submits", async ({
    page,
  }) => {
    // Regression: when display_value=True, the widget used to emit both a
    // visible search input and a hidden sibling with the same `name`. The
    // browser submitted both, and the hidden's empty value won. The form
    // received `adresse=""` and the page never recovered the picked label.
    await navigateTo(page, "/carte")

    const named = page.locator(`input[name="${ADRESSE_FIELD_NAME}"]`)
    await expect(named).toHaveCount(1)
    await expect(named).toHaveAttribute("type", "search")
  })

  test("submitting the form sends carte_map-adresse populated with the picked label", async ({
    page,
  }) => {
    await navigateTo(page, "/carte")

    // Capture the next form submission triggered by the address pick.
    const submitRequest = page.waitForRequest(
      (request) =>
        request.method() === "GET" &&
        request.url().includes("/carte?") &&
        request.url().includes(`${ADRESSE_FIELD_NAME}=`),
      { timeout: TIMEOUT.DEFAULT },
    )

    await pickFirstAddress(page, "Auray")

    const request = await submitRequest
    const url = new URL(request.url())
    expect(url.searchParams.get(ADRESSE_FIELD_NAME)).toBe("Auray")
    expect(url.searchParams.get("carte_map-latitude")).toBe("47.668099")
    expect(url.searchParams.get("carte_map-longitude")).toBe("-2.990838")
  })

  test("picking a new address clears a stale bbox left by the map controller", async ({
    page,
  }) => {
    // Regression: after the user pans the map, the search-solution-form's
    // bounding_box hidden field carries the new map view. Picking a fresh
    // address must clear that bbox before submitting — otherwise the server
    // gives precedence to bbox over lat/lon and returns acteurs scoped to
    // the previous map view (the original "Auray markers stay after picking
    // Montbéliard" bug). state#setLocation owns the reset; the form's own
    // listener was removed to avoid a race that submitted before bbox was
    // cleared.
    await navigateTo(page, "/carte")
    await pickFirstAddress(page, "Auray")

    // Simulate the map controller having written a bbox after a pan.
    await page.evaluate(() => {
      const bbox = document.querySelector<HTMLInputElement>(
        '[data-search-solution-form-target="bbox"]',
      )
      if (!bbox) throw new Error("no bbox target")
      const setter = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )?.set
      setter?.call(
        bbox,
        JSON.stringify({
          southWest: { lat: 47.4, lng: 6.6 },
          northEast: { lat: 47.6, lng: 7.0 },
        }),
      )
      bbox.dispatchEvent(new Event("input", { bubbles: true }))
    })

    // Capture the GET that fires when the user picks a new address.
    const submitRequest = page.waitForRequest(
      (request) =>
        request.method() === "GET" &&
        request.url().includes("/carte?") &&
        request.url().includes(`${ADRESSE_FIELD_NAME}=Auray`),
      { timeout: TIMEOUT.DEFAULT },
    )

    // Re-pick (same address — also exercises the case where the visible
    // input value already matches the new pick).
    const input = page.locator(CARTE_INPUT)
    await input.click()
    await input.fill("Auray")
    await page.locator(CARTE_OPTION).filter({ hasText: "Auray" }).first().click()

    const url = new URL((await submitRequest).url())
    expect(url.searchParams.get("carte_map-bounding_box")).toBe("")
    expect(url.searchParams.get(ADRESSE_FIELD_NAME)).toBe("Auray")
  })

  test("reloading after picking an address does not re-submit in a loop", async ({
    page,
  }) => {
    // Repro of the original loop: pick an address, reload, observe that the
    // page settles and does NOT keep firing GET /carte requests.
    await navigateTo(page, "/carte")
    await pickFirstAddress(page, "Auray")

    // Reload and count submits to /carte over a short observation window.
    // Filter to actual form submissions (carry the adresse param) so the
    // initial page-load request and unrelated traffic don't pollute the count.
    const submitsAfterReload: string[] = []
    page.on("request", (request) => {
      const url = request.url()
      if (
        request.method() === "GET" &&
        url.includes("/carte?") &&
        url.includes(`${ADRESSE_FIELD_NAME}=`)
      ) {
        submitsAfterReload.push(url)
      }
    })

    await page.reload()
    // Give state.ts and the form's data-action plenty of time to misfire.
    // The original bug submitted dozens of times within this window.
    await page.waitForTimeout(3000)

    expect(submitsAfterReload.length).toBeLessThanOrEqual(2)
    // Every submit must carry the picked address — proves the field is no
    // longer serializing as empty (which used to trigger the loop).
    for (const url of submitsAfterReload) {
      expect(url).toMatch(new RegExp(`${ADRESSE_FIELD_NAME}=Auray`))
    }
  })
})
