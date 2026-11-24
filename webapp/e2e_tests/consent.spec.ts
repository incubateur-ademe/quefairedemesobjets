import { execSync } from "child_process"
import { expect, Page, test } from "@playwright/test"

const SIX_MONTHS_IN_SECONDS = 183 * 24 * 60 * 60
const ONE_DAY_IN_SECONDS = 24 * 60 * 60

// The banner is switched on from the Wagtail admin (CustomScriptsSettings).
function setBannerEnabled(isEnabled: boolean) {
  const python = [
    "from wagtail.models import Site",
    "from sites_conformes.content_manager.models import CustomScriptsSettings",
    "[CustomScriptsSettings.objects.update_or_create(site=site, " +
      `defaults={'use_tarteaucitron': ${isEnabled ? "True" : "False"}}) ` +
      "for site in Site.objects.all()]",
  ].join("; ")
  execSync(`uv run python manage.py shell -c "${python}"`, {
    env: {
      ...process.env,
      DATABASE_URL: process.env.DB_WEBAPP_SAMPLE ?? process.env.DATABASE_URL,
    },
    stdio: "pipe",
  })
}

// tarteaucitron binds its click handlers shortly after it shows the banner.
async function answer(page: Page, buttonId: string) {
  const banner = page.locator("#tarteaucitronAlertBig")
  await expect(async () => {
    await page.locator(buttonId).click()
    await expect(banner).toBeHidden({ timeout: 500 })
  }).toPass()
}

async function posthogCookie(page: Page) {
  const cookies = await page.context().cookies()
  return cookies.find(({ name }) => /^ph_.*_posthog$/.test(name))
}

function distinctId(cookieValue: string): string {
  return JSON.parse(decodeURIComponent(cookieValue)).distinct_id
}

test.describe("🍪 Consentement aux cookies", () => {
  test.beforeAll(() => setBannerEnabled(true))
  test.afterAll(() => setBannerEnabled(false))

  test("the banner asks for consent and nothing is stored before an answer", async ({
    page,
  }) => {
    await page.goto("/")
    await expect(page.locator("#tarteaucitronAlertBig")).toBeVisible()
    expect(await posthogCookie(page)).toBeUndefined()
  })

  test("refusing leaves no PostHog cookie", async ({ page }) => {
    await page.goto("/")
    await answer(page, "#tarteaucitronAllDenied2")
    await page.reload()
    await expect(page.locator("#tarteaucitronAlertBig")).toBeHidden()
    expect(await posthogCookie(page)).toBeUndefined()
  })

  test("accepting keeps the same PostHog identifier across page loads", async ({
    page,
  }) => {
    await page.goto("/")
    await answer(page, "#tarteaucitronPersonalize2")
    await expect.poll(() => posthogCookie(page)).toBeDefined()
    const firstId = distinctId((await posthogCookie(page))!.value)

    await page.reload()
    await expect(page.locator("#tarteaucitronAlertBig")).toBeHidden()
    const secondId = distinctId((await posthogCookie(page))!.value)
    expect(secondId).toBe(firstId)
    expect(secondId).not.toBe("$posthog_cookieless")
  })

  test("the consent is asked again after six months", async ({ page }) => {
    await page.goto("/")
    await answer(page, "#tarteaucitronAllDenied2")
    const cookies = await page.context().cookies()
    const consent = cookies.find(({ name }) => name === "tarteaucitron")!
    const lifetime = consent.expires - Date.now() / 1000
    expect(Math.abs(lifetime - SIX_MONTHS_IN_SECONDS)).toBeLessThan(ONE_DAY_IN_SECONDS)
  })

  test("the footer button reopens the panel", async ({ page }) => {
    await page.goto("/")
    await answer(page, "#tarteaucitronAllDenied2")
    await page.locator("#tarteaucitronManager").click()
    await expect(page.locator("#tarteaucitron")).toBeVisible()
    await expect(page.locator("#posthogqfLine")).toBeVisible()
  })

  test("no banner inside an iframe", async ({ page }) => {
    await page.setContent(
      `<iframe src="http://localhost:8888/" width="800" height="600"></iframe>`,
    )
    const frame = page.frameLocator("iframe")
    await expect(frame.locator("main")).toBeVisible()
    await expect(frame.locator("#tarteaucitronAlertBig")).toHaveCount(0)
    expect(await posthogCookie(page)).toBeUndefined()
  })
})
