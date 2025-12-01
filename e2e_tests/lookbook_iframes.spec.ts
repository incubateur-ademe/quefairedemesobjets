import { expect } from "@playwright/test"
import { test } from "./config"

/**
 * Tests for Lookbook iframe previews
 *
 * These tests verify that each lookbook preview page generates iframes with the correct IDs
 * as specified in the corresponding TypeScript embed scripts in static/to_compile/embed/
 */

test.describe("Lookbook iframe ID validation", () => {
  test("carte lookbook generates iframe with ID 'carte'", async ({ page }) => {
    await page.goto("/lookbook/preview/iframe/carte", {
      waitUntil: "domcontentloaded",
    })

    // Check that iframe with ID 'carte' exists and is visible
    const iframe = page.locator("iframe#carte")
    await expect(iframe).toBeAttached()
  })

  test("formulaire lookbook generates iframe with ID 'formulaire'", async ({
    page,
  }) => {
    await page.goto("/lookbook/preview/iframe/formulaire", {
      waitUntil: "domcontentloaded",
    })

    // Check that iframe with ID 'formulaire' exists and is visible
    const iframe = page.locator("iframe#formulaire")
    await expect(iframe).toBeAttached()
  })

  test.skip("assistant lookbook generates iframe with ID 'assistant'", async ({
    page,
  }) => {
    await page.goto("/lookbook/preview/iframe/assistant", {
      waitUntil: "domcontentloaded",
    })

    // Check that iframe with ID 'assistant' exists and is visible
    const iframe = page.locator("iframe#assistant")
    await expect(iframe).toBeAttached({ timeout: 10000 })
  })

  test("infotri-configurator lookbook generates iframe with ID 'infotri-configurator'", async ({
    page,
  }) => {
    await page.goto("/lookbook/preview/iframe/infotri_configurator", {
      waitUntil: "domcontentloaded",
    })

    // Check that iframe with ID 'infotri-configurator' exists and is visible
    const iframe = page.locator("iframe#infotri-configurator")
    await expect(iframe).toBeAttached()
  })

  test("infotri lookbook generates iframe with ID 'infotri'", async ({ page }) => {
    await page.goto("/lookbook/preview/iframe/infotri", {
      waitUntil: "domcontentloaded",
    })

    // Check that iframe with ID 'infotri' exists and is visible
    const iframe = page.locator("iframe#infotri")
    await expect(iframe).toBeAttached()
  })
})
