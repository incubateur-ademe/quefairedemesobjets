import { AxeBuilder } from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// Shared variables
const BASE_URL = "https://assistant.dev";
const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];
const IFRAME_SELECTOR = "iframe";

test.describe("WCAG Compliance Tests", () => {
  test("Formulaire iFrame | Desktop", async ({ page }) => {
    await page.goto(`${BASE_URL}/test_iframe`, { waitUntil: "networkidle" });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include(IFRAME_SELECTOR) // Restrict scan to the iframe
      .withTags(WCAG_TAGS)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Carte iFrame | Desktop", async ({ page }) => {
    await page.goto(`${BASE_URL}/test_iframe?carte`, { waitUntil: "networkidle" });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include(IFRAME_SELECTOR) // Restrict scan to the iframe
      .withTags(WCAG_TAGS)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Assistant Homepage | Desktop", async ({ page }) => {
    // TODO: Update the route for production
    await page.goto(`${BASE_URL}/`, { waitUntil: "networkidle" });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .exclude("[data-disable-axe]")
      .withTags(WCAG_TAGS)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Assistant Detail Page | Desktop", async ({ page }) => {
    await page.goto(`${BASE_URL}/smartphone`, { waitUntil: "networkidle" });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .exclude("[data-disable-axe]")
      .withTags(WCAG_TAGS)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
