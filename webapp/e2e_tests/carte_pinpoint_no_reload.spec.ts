import { expect, type Response } from "@playwright/test"
import { test } from "./fixtures"
import {
  clickFirstClickableActeurMarker,
  mockApiAdresse,
  navigateTo,
  searchForAuray,
  TIMEOUT,
} from "./helpers"

/**
 * Regression guard for the A/B-testing pinpoint bug.
 *
 * Clicking a pinpoint must navigate ONLY the nested acteur-detail frame. It must
 * NOT trigger a submit/reload of the carte frame (the former Stimulus-outlet
 * lifecycle callback re-fired on the Turbo re-render and re-submitted the form,
 * which — under the A/B experiment — reloaded the carte as the "liste" variant
 * and discarded the acteur detail).
 *
 * We assert two things after a pinpoint click:
 *  1. the acteur-detail panel opens (the intended navigation happened), and
 *  2. the carte content did NOT re-render — a sentinel set on the carte form
 *     before the click survives, AND no new carte-frame fetch is issued.
 */
test.describe("🗺️ Pinpoint click does not reload the carte", () => {
  test("clicking a pinpoint only opens the acteur detail, no carte reload", async ({
    page,
  }) => {
    await navigateTo(page, "/carte")
    await mockApiAdresse(page)
    await searchForAuray(page)

    // Stay in carte mode and confirm pinpoints are present.
    const markers = page.locator(
      '.maplibregl-marker[data-controller="pinpoint"]:not(#pinpoint-home)',
    )
    await expect(markers.first()).toBeVisible({ timeout: TIMEOUT.LONG })

    // Place a sentinel on the carte form. If the carte frame reloads, the form
    // is re-rendered from the server response and the sentinel is gone.
    await page
      .locator('form[data-controller~="search-solution-form"]')
      .evaluate((form) => form.setAttribute("data-reload-sentinel", "present"))

    // Track any carte-frame fetch (the phantom submit) AFTER the click.
    let carteFrameReloaded = false
    const onResponse = (response: Response) => {
      const turboFrame = response.request().headers()["turbo-frame"]
      if (
        response.url().includes("/carte") &&
        turboFrame !== undefined &&
        turboFrame !== ""
      ) {
        carteFrameReloaded = true
      }
    }
    page.on("response", onResponse)

    await clickFirstClickableActeurMarker(page)

    // (1) intended navigation happened.
    await expect(page.locator("#acteurDetailsPanel")).toHaveAttribute(
      "aria-hidden",
      "false",
      { timeout: TIMEOUT.DEFAULT },
    )

    // Give any spurious submit a chance to fire before asserting it did not.
    await page.waitForTimeout(1000)
    page.off("response", onResponse)

    // (2a) carte form was not re-rendered.
    await expect(
      page.locator('form[data-controller~="search-solution-form"]'),
    ).toHaveAttribute("data-reload-sentinel", "present")

    // (2b) no carte-frame fetch was triggered by the click.
    expect(carteFrameReloaded).toBe(false)

    // Still in carte mode (no switch to liste).
    await expect(page.getByTestId("liste-mode-container")).toHaveCount(0)
  })
})
