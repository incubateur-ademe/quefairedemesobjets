import { execSync } from "node:child_process"
import { expect, Page } from "@playwright/test"
import { test } from "./fixtures"
import { navigateTo, TIMEOUT } from "./helpers"

const FLAG_KEY = "produit-carte-default-view-mobile"
const PRODUIT_SLUG = "meubles"
const PRODUIT_PATH = `/categories/${PRODUIT_SLUG}/`

/**
 * Opt the sample ProduitPage into the experiment for the duration of these
 * tests, then revert. The Django dev server started by `webServer` shares
 * the same DB, so this is the simplest reliable way to seed data without
 * adding a management command.
 */
function setAbOptIn(slug: string, enabled: boolean) {
  const code = [
    "from qfdmd.models import ProduitPage",
    `ProduitPage.objects.filter(slug='${slug}').update(ab_test_carte_default_view=${enabled ? "True" : "False"})`,
  ].join("; ")
  execSync(`uv run python manage.py shell -c "${code}"`, { stdio: "pipe" })
}

/**
 * Stub PostHog's `/decide` and `/flags/` endpoints so that the named flag
 * resolves to the requested variant for the duration of the test.
 *
 * We don't know which exact api_host is used (defaults to "/ph" locally,
 * eu.posthog.com in CI), so we match any URL that contains the path.
 */
async function stubPosthogFlag(page: Page, flagKey: string, value: string) {
  const matchPosthogDecide = (url: URL) =>
    url.pathname.endsWith("/decide/") || url.pathname.endsWith("/flags/")

  await page.route(
    (url) => matchPosthogDecide(url),
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          featureFlags: { [flagKey]: value },
          featureFlagPayloads: {},
          sessionRecording: false,
          isAuthenticated: false,
          supportedCompression: [],
          config: { enable_collect_everything: false },
          toolbarParams: {},
          siteApps: [],
          capturePerformance: false,
          autocapture_opt_out: true,
          autocaptureExceptions: false,
        }),
      })
    },
  )
  // Block /e/ (capture events) so they don't 404 the test logs.
  await page.route(
    (url) => url.pathname.endsWith("/e/") || url.pathname.endsWith("/i/v0/e/"),
    async (route) => route.fulfill({ status: 200, body: "1" }),
  )
}

async function getCarteFrameSrc(page: Page): Promise<string | null> {
  const frame = page.locator("turbo-frame[data-testid='carte']")
  await expect(frame).toBeAttached({ timeout: TIMEOUT.DEFAULT })
  // Wait until the controller has set the src (or restored it).
  // Initial markup has src=control; controller temporarily clears it then reassigns.
  await page.waitForFunction(
    () => {
      const f = document.querySelector("turbo-frame[data-testid='carte']")
      return f?.getAttribute("src") || null
    },
    null,
    { timeout: TIMEOUT.DEFAULT },
  )
  return frame.getAttribute("src")
}

test.beforeAll(() => setAbOptIn(PRODUIT_SLUG, true))
test.afterAll(() => setAbOptIn(PRODUIT_SLUG, false))

test.describe("AB test: produit carte default view (mobile)", () => {
  test.use({ viewport: { width: 375, height: 812 } })

  test("variant flag adds view_mode-view=liste to the carte frame on mobile", async ({
    page,
  }) => {
    await stubPosthogFlag(page, FLAG_KEY, "variant")
    await navigateTo(page, PRODUIT_PATH)

    const src = await getCarteFrameSrc(page)
    expect(src).toContain("view_mode-view=liste")
  })

  test("control flag keeps the original carte frame src", async ({ page }) => {
    await stubPosthogFlag(page, FLAG_KEY, "control")
    await navigateTo(page, PRODUIT_PATH)

    const src = await getCarteFrameSrc(page)
    expect(src).not.toContain("view_mode-view=liste")
  })
})

test.describe("AB test: produit carte default view (desktop)", () => {
  test.use({ viewport: { width: 1280, height: 800 } })

  test("desktop ignores the variant (mobile-only gate)", async ({ page }) => {
    await stubPosthogFlag(page, FLAG_KEY, "variant")
    await navigateTo(page, PRODUIT_PATH)

    const src = await getCarteFrameSrc(page)
    expect(src).not.toContain("view_mode-view=liste")
  })
})
