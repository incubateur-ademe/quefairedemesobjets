import { test as base, expect, chromium, BrowserContext } from "@playwright/test"
import * as path from "path"
import * as dotenv from "dotenv"

dotenv.config({ path: path.resolve(__dirname, "../.env") })

const EXTENSION_PATH = path.resolve(__dirname, "../chrome-extension/dist_chrome")
const BASE_URL = process.env.BASE_URL!

const TIMEOUT = {
  SHORT: 5000,
  DEFAULT: 10000,
  LONG: 30000,
}

/**
 * Custom test fixture that launches Chromium with the QFDMO Inspector
 * chrome extension loaded via --load-extension.
 *
 * Extensions require a persistent context (cannot use headless mode).
 */
const test = base.extend<{
  context: BrowserContext
  extensionId: string
}>({
  // eslint-disable-next-line no-empty-pattern
  context: async ({}, use) => {
    const context = await chromium.launchPersistentContext("", {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
        "--ignore-certificate-errors",
      ],
    })
    await use(context)
    await context.close()
  },
  extensionId: async ({ context }, use) => {
    let [background] = context.serviceWorkers()
    if (!background) background = await context.waitForEvent("serviceworker")
    const extensionId = background.url().split("/")[2]
    await use(extensionId)
  },
})

/**
 * Helper: open a target page then the extension popup.
 * The popup queries the active tab for analysis results.
 */
async function openPopupForPage(
  context: BrowserContext,
  extensionId: string,
  targetUrl: string,
) {
  // Open the target page first (becomes the active tab)
  const targetPage = await context.newPage()
  await targetPage.goto(targetUrl, { waitUntil: "domcontentloaded" })

  // Wait for iframes to be injected by the embed script
  await targetPage
    .waitForSelector("iframe", { timeout: TIMEOUT.DEFAULT })
    .catch(() => {})
  await targetPage.waitForTimeout(1000)

  // Open popup as a new page (the popup queries the active tab)
  const popup = await context.newPage()
  await popup.goto(`chrome-extension://${extensionId}/src/pages/popup/index.html`, {
    waitUntil: "domcontentloaded",
  })

  return { targetPage, popup }
}

test.describe("🧩 Extension Chrome - Detection des iframes QFDMO", () => {
  test.describe("🗺️ Carte", () => {
    test("Detecte l'iframe carte sur la page lookbook", async ({
      context,
      extensionId,
    }) => {
      const { targetPage, popup } = await openPopupForPage(
        context,
        extensionId,
        `${BASE_URL}/lookbook/preview/iframe/carte`,
      )

      // Should detect 1 iframe
      await expect(
        popup.locator(".fr-badge").filter({ hasText: /1 iframe/ }),
      ).toBeVisible({ timeout: TIMEOUT.DEFAULT })

      // Should show "Carte" type
      await expect(
        popup.locator(".fr-badge").filter({ hasText: "Carte" }),
      ).toBeVisible()

      // Should detect adjacent script (carte.js)
      await expect(popup.locator("text=Via script")).toBeVisible()

      // Should show script filename
      await expect(popup.locator("text=carte.js")).toBeVisible()

      // Should detect iframe-resizer (carte.js bundles it)
      // Wait for auto-refresh to pick up the iframe-resizer status
      await expect(popup.locator(".fr-tag").filter({ hasText: "Detecte" })).toBeVisible(
        { timeout: TIMEOUT.LONG },
      )

      await targetPage.close()
      await popup.close()
    })
  })

  test.describe("🗺️ Carte sur mesure", () => {
    test("Detecte l'iframe carte sur mesure avec le slug", async ({
      context,
      extensionId,
    }) => {
      const { targetPage, popup } = await openPopupForPage(
        context,
        extensionId,
        `${BASE_URL}/lookbook/preview/iframe/carte_sur_mesure`,
      )

      await expect(popup.locator(".fr-card")).toBeVisible({ timeout: TIMEOUT.DEFAULT })

      // Should show "Carte sur mesure" type
      await expect(
        popup.locator(".fr-badge").filter({ hasText: "Carte sur mesure" }),
      ).toBeVisible()

      // Should display the slug (default is "cyclevia")
      await expect(
        popup.locator(".fr-badge").filter({ hasText: "cyclevia" }),
      ).toBeVisible()

      // Should have adjacent script
      await expect(popup.locator("text=Via script")).toBeVisible()

      // Should have "Admin carte" button for carte sur mesure
      await expect(popup.locator("text=Admin carte")).toBeVisible()

      // Should also have "Ouvrir l'iframe" button
      await expect(popup.locator("text=Ouvrir l'iframe")).toBeVisible()

      await targetPage.close()
      await popup.close()
    })
  })

  test.describe("🗺️ Carte preconfiguree", () => {
    test("Detecte l'iframe carte preconfiguree avec data-attributes", async ({
      context,
      extensionId,
    }) => {
      const { targetPage, popup } = await openPopupForPage(
        context,
        extensionId,
        `${BASE_URL}/lookbook/preview/iframe/carte_preconfiguree`,
      )

      await expect(popup.locator(".fr-card")).toBeVisible({ timeout: TIMEOUT.DEFAULT })

      // Should show "Carte preconfiguree" type (carte with data-attributes, no slug)
      await expect(
        popup.locator(".fr-badge").filter({ hasText: "Carte preconfiguree" }),
      ).toBeVisible()

      // Should show data-attributes section
      await expect(popup.locator("text=Data-attributes")).toBeVisible()
      await expect(popup.locator("text=data-action_displayed")).toBeVisible()

      // Should have adjacent script
      await expect(popup.locator("text=Via script")).toBeVisible()

      // Should warn about using carte sur mesure instead
      await expect(
        popup.locator("text=envisagez d'utiliser une carte sur mesure"),
      ).toBeVisible()

      await targetPage.close()
      await popup.close()
    })
  })

  test.describe("🤖 Assistant", () => {
    test("Detecte l'iframe assistant", async ({ context, extensionId }) => {
      const { targetPage, popup } = await openPopupForPage(
        context,
        extensionId,
        `${BASE_URL}/lookbook/preview/iframe/assistant`,
      )

      await expect(popup.locator(".fr-card")).toBeVisible({ timeout: TIMEOUT.DEFAULT })

      // Should show "Assistant" type
      await expect(
        popup.locator(".fr-badge").filter({ hasText: "Assistant" }),
      ).toBeVisible()

      // Should have adjacent script (iframe.js)
      await expect(popup.locator("text=Via script")).toBeVisible()
      await expect(popup.locator("text=iframe.js")).toBeVisible()

      // Should detect iframe-resizer (iframe.js bundles it)
      await expect(popup.locator(".fr-tag").filter({ hasText: "Detecte" })).toBeVisible(
        { timeout: TIMEOUT.LONG },
      )

      await targetPage.close()
      await popup.close()
    })
  })

  test.describe("📋 Formulaire", () => {
    test("Detecte l'iframe formulaire comme type assistant", async ({
      context,
      extensionId,
    }) => {
      const { targetPage, popup } = await openPopupForPage(
        context,
        extensionId,
        `${BASE_URL}/lookbook/preview/iframe/formulaire`,
      )

      await expect(popup.locator(".fr-card")).toBeVisible({ timeout: TIMEOUT.DEFAULT })

      // Formulaire uses iframe.js with route "formulaire" -> detected as "Assistant"
      await expect(
        popup.locator(".fr-badge").filter({ hasText: "Assistant" }),
      ).toBeVisible()

      // Should have adjacent script
      await expect(popup.locator("text=Via script")).toBeVisible()

      // Should show data-attributes from the script tag
      await expect(popup.locator("text=Data-attributes")).toBeVisible()

      await targetPage.close()
      await popup.close()
    })
  })

  test.describe("🚫 Page sans iframe", () => {
    test("Affiche un message quand il n'y a pas d'iframe QFDMO", async ({
      context,
      extensionId,
    }) => {
      const { targetPage, popup } = await openPopupForPage(
        context,
        extensionId,
        `${BASE_URL}/lookbook/`,
      )

      // Should show "no iframe" message
      await expect(popup.locator("text=Aucune iframe QFDMO detectee")).toBeVisible({
        timeout: TIMEOUT.DEFAULT,
      })

      await targetPage.close()
      await popup.close()
    })
  })
})
