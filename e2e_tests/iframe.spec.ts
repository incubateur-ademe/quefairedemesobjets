import { expect } from "@playwright/test"
import { test } from "./config"

test.describe("📦 Système d'Intégration Iframe", () => {
  test.describe("Validation des ID d'iframe", () => {
    test("carte lookbook generates iframe with ID 'carte'", async ({ page }) => {
      await page.goto("/lookbook/preview/iframe/carte", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#carte")
      await expect(iframe).toBeAttached({ timeout: 10000 })
    })

    test("formulaire lookbook generates iframe with ID 'formulaire'", async ({
      page,
    }) => {
      await page.goto("/lookbook/preview/iframe/formulaire", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#formulaire")
      await expect(iframe).toBeAttached({ timeout: 10000 })
    })

    test("assistant lookbook generates iframe with ID 'assistant'", async ({
      page,
    }) => {
      await page.goto("/lookbook/preview/iframe/assistant", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#assistant")
      await expect(iframe).toBeAttached({ timeout: 10000 })
    })

    test("infotri-configurator lookbook generates iframe with ID 'infotri-configurator'", async ({
      page,
    }) => {
      await page.goto("/lookbook/preview/iframe/infotri_configurator", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#infotri-configurator")
      await expect(iframe).toBeAttached()
    })

    test("infotri lookbook generates iframe with ID 'infotri'", async ({ page }) => {
      await page.goto("/lookbook/preview/iframe/infotri", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#infotri")
      await expect(iframe).toBeAttached()
    })
  })

  test.describe("Iframe formulaire", () => {
    test("is loaded with correct parameters", async ({ page, baseUrl }) => {
      await page.goto(`/lookbook/preview/iframe/formulaire/`, {
        waitUntil: "domcontentloaded",
      })

      const iframeElement = await page.$("iframe#formulaire")
      const attributes = await Promise.all([
        iframeElement?.getAttribute("allow"),
        iframeElement?.getAttribute("src"),
        iframeElement?.getAttribute("frameborder"),
        iframeElement?.getAttribute("scrolling"),
        iframeElement?.getAttribute("allowfullscreen"),
        iframeElement?.getAttribute("style"),
        iframeElement?.getAttribute("title"),
      ])

      const [allow, src, frameborder, scrolling, allowfullscreen, style, title] =
        attributes

      expect(allow).toBe("geolocation; clipboard-write")
      expect(src).toBe(
        `${baseUrl}/formulaire?direction=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
      )
      expect(frameborder).toBe("0")
      expect(scrolling).toBe("no")
      expect(allowfullscreen).toBe("true")
      expect(style).toContain("width: 100%;")
      expect(style).toContain("height: 720px;")
      expect(style).toContain("max-width: 100%;")
      expect(title).toBe("Longue vie aux objets")
    })

    test("form is visible in the iframe", async ({ page }) => {
      await page.goto(`/lookbook/preview/iframe/formulaire/`, {
        waitUntil: "domcontentloaded",
      })

      const iframeElement = page.frameLocator("iframe#formulaire")

      const form = iframeElement.locator("#search_form")
      await expect(form).toBeVisible({ timeout: 10000 })

      const formHeight = await iframeElement
        .locator("[data-testid='form-content']")
        .evaluate((el) => el.offsetHeight)
      expect(formHeight).toBeGreaterThan(600)
    })
  })

  test.describe("Iframe carte", () => {
    test("displays correctly", async ({ page }) => {
      await page.goto(`/lookbook/preview/iframe/carte/`, {
        waitUntil: "domcontentloaded",
      })

      await page.waitForTimeout(2000)

      await expect(page).toHaveScreenshot("iframe-carte.png", { timeout: 10000 })
    })
  })

  test.describe("Iframe assistant", () => {
    test("displays correctly", async ({ page }) => {
      test.slow()
      await page.goto(`/lookbook/preview/iframe/assistant/`, {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#assistant")

      await expect(iframe).toHaveAttribute("allow", /geolocation/)
    })
  })

  test.describe("URLs iframe legacy", () => {
    test("still work", async ({ page }) => {
      await page.goto(
        `/formulaire?direction=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
        { waitUntil: "domcontentloaded" },
      )
      await expect(page).toHaveURL(
        `/formulaire?direction=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
      )
      await page.goto(
        `/carte?action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50`,
        { waitUntil: "domcontentloaded" },
      )
      await expect(page).toHaveURL(
        `/carte?action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50`,
      )
    })
  })

  test.describe("Persistance mode iframe", () => {
    test("persists across navigation", async ({ page, baseUrl }) => {
      test.slow()
      await page.goto(`/?iframe`, { waitUntil: "domcontentloaded" })
      expect(page).not.toBeNull()

      for (let i = 0; i < 50; i++) {
        await expect(page.locator("body")).toHaveAttribute(
          "data-state-iframe-value",
          "true",
        )

        const links = page.locator(`a[href^="${baseUrl}"]`)

        const count = await links.count()
        const randomLink = links.nth(Math.floor(Math.random() * count))
        if (await randomLink.isVisible()) {
          await randomLink.click()
        }
      }
    })
  })
})
test.describe("📜 Vérification des scripts", () => {
  /**
   * Tests for embed script routes
   *
   * These tests verify that all embed script files are accessible
   * and return the correct content type.
   */

  test("carte.js script is accessible", async ({ page, baseUrl }) => {
    const response = await page.goto(`${baseUrl}/static/carte.js`)
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("iframe.js script is accessible", async ({ page, baseUrl }) => {
    const response = await page.goto(`${baseUrl}/static/iframe.js`)
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("infotri.js script is accessible", async ({ page, baseUrl }) => {
    const response = await page.goto(`${baseUrl}/iframe.js`)
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("configurateur.js script is accessible", async ({ page, baseUrl }) => {
    const response = await page.goto(`${baseUrl}/infotri/configurateur.js`)
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })
})
