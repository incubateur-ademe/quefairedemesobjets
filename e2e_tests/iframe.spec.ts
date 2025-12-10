import { test, expect } from "@playwright/test"

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
    test("is loaded with correct parameters", async ({ page, baseURL }) => {
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
        `${baseURL}/formulaire?direction=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
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
    test("persists across navigation", async ({ page, baseURL }) => {
      test.slow()
      await page.goto(`/?iframe`, { waitUntil: "domcontentloaded" })
      expect(page).not.toBeNull()

      for (let i = 0; i < 50; i++) {
        await expect(page.locator("body")).toHaveAttribute(
          "data-state-iframe-value",
          "true",
        )

        const links = page.locator(`a[href^="${baseURL}"]`)

        const count = await links.count()
        const randomLink = links.nth(Math.floor(Math.random() * count))
        if (await randomLink.isVisible()) {
          await randomLink.click()
        }
      }
    })
  })

  test.describe("Referrer tracking in iframe", () => {
    test("tracks parent referrer correctly when clicking links inside iframe", async ({
      page,
    }) => {
      // Navigate to the test page
      await page.goto(
        "/lookbook/preview/tests/referrer/?timestamp=1765378324992&display=%257B%2522theme%2522%253A%2522light%2522%257D",
        { waitUntil: "domcontentloaded" },
      )

      // Get the parent window location for comparison
      const parentLocation = page.url()

      // Locate the test iframe
      const iframe = page.frameLocator("iframe#test")

      // Wait for iframe content to load and analytics controller to initialize
      await iframe.locator("body").waitFor({ timeout: 10000 })

      // Wait a bit for the analytics controller to fully initialize
      await page.waitForTimeout(500)

      // Find and click any visible link inside the iframe
      const links = iframe.locator("a")
      const linkCount = await links.count()

      // Ensure there's at least one link
      expect(linkCount).toBeGreaterThan(0)

      // Find the first visible link
      let clickedLink = false
      for (let i = 0; i < linkCount; i++) {
        const link = links.nth(i)
        if (await link.isVisible()) {
          await link.click()
          clickedLink = true
          break
        }
      }

      // If no visible link found, just click the first one and scroll to it
      if (!clickedLink) {
        const firstLink = links.first()
        await firstLink.scrollIntoViewIfNeeded()
        await firstLink.click()
      }

      // Wait for navigation to complete inside the iframe
      await page.waitForTimeout(1000)

      // Wait for the body to be present after navigation
      await iframe.locator("body").waitFor({ timeout: 10000 })

      // Wait for analytics controller to initialize after navigation
      await page.waitForTimeout(500)

      // Execute JavaScript inside the iframe to get personProperties
      const personProperties = await iframe.locator("body").evaluate(() => {
        const controller = (
          window as any
        ).stimulus?.getControllerForElementAndIdentifier(
          document.querySelector("body"),
          "analytics",
        )
        if (!controller) {
          return null
        }
        return controller.personProperties
      })

      // Verify analytics controller is loaded
      expect(personProperties).not.toBeNull()

      // Verify that iframe is set to true
      expect(personProperties.iframe).toBe(true)

      // Verify that iframeReferrer is set and matches the parent window location
      expect(personProperties.iframeReferrer).toBeDefined()
      expect(personProperties.iframeReferrer).toBe(parentLocation)
    })
  })
})
test.describe("📜 Vérification des scripts", () => {
  /**
   * Tests for embed script routes
   *
   * These tests verify that all embed script files are accessible
   * and return the correct content type using HTTP fetch.
   */

  test("carte.js script is accessible", async ({ page }) => {
    const response = await page.goto("/static/carte.js")
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("iframe.js script is accessible", async ({ page }) => {
    const response = await page.goto("/static/iframe.js")
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("infotri.js script is accessible", async ({ page }) => {
    const response = await page.goto("/iframe.js")
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("configurateur.js script is accessible", async ({ page }) => {
    const response = await page.goto("/infotri/configurateur.js")
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })
})
