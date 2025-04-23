import { AxeBuilder } from "@axe-core/playwright";
import { expect } from "@playwright/test";
import { test } from "./config"

// Shared variables
const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];
const IFRAME_SELECTOR = "iframe";

test.describe("WCAG Compliance Tests", () => {
  test("Formulaire iFrame | Desktop", async ({ page }) => {
    await page.goto(`/test_iframe`, { waitUntil: "networkidle" });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include(IFRAME_SELECTOR) // Restrict scan to the iframe
      .withTags(WCAG_TAGS)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Carte iFrame | Desktop", async ({ page }) => {
    await page.goto(`/test_iframe?carte`, { waitUntil: "networkidle" });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include(IFRAME_SELECTOR) // Restrict scan to the iframe
      .withTags(WCAG_TAGS)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Assistant Homepage | Desktop", async ({ page }) => {
    // TODO: Update the route for production
    await page.goto(`/`, { waitUntil: "networkidle" });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .exclude("[data-disable-axe]")
      .withTags(WCAG_TAGS)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Assistant Detail Page | Desktop", async ({ page, assistantUrl }) => {
    await page.goto(`${assistantUrl}/dechet/smartphone`, { waitUntil: "networkidle" });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .exclude("[data-disable-axe]")
      .withTags(WCAG_TAGS)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
