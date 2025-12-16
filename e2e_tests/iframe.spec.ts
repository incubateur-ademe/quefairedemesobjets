import { test, expect } from "@playwright/test"

test.describe("📦 Système d'Intégration Iframe", () => {
  test.describe("Génération des iframes avec ID corrects", () => {
    test("L'iframe de la carte a l'ID 'carte'", async ({ page }) => {
      await page.goto("/lookbook/preview/iframe/carte", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#carte")
      await expect(iframe).toBeAttached({ timeout: 10000 })
    })

    test("L'iframe du formulaire a l'ID 'formulaire'", async ({ page }) => {
      await page.goto("/lookbook/preview/iframe/formulaire", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#formulaire")
      await expect(iframe).toBeAttached({ timeout: 10000 })
    })

    test("L'iframe de l'assistant a l'ID 'assistant'", async ({ page }) => {
      await page.goto("/lookbook/preview/iframe/assistant", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#assistant")
      await expect(iframe).toBeAttached({ timeout: 10000 })
    })

    test("L'iframe du configurateur infotri a l'ID 'infotri-configurator'", async ({
      page,
    }) => {
      await page.goto("/lookbook/preview/iframe/infotri_configurator", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#infotri-configurator")
      await expect(iframe).toBeAttached()
    })

    test("L'iframe infotri a l'ID 'infotri'", async ({ page }) => {
      await page.goto("/lookbook/preview/iframe/infotri", {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#infotri")
      await expect(iframe).toBeAttached()
    })
  })

  test.describe("Configuration de l'iframe formulaire", () => {
    test("L'iframe est chargée avec les bons paramètres et attributs", async ({
      page,
      baseURL,
    }) => {
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

    test("Le formulaire est visible et a la bonne hauteur dans l'iframe", async ({
      page,
    }) => {
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

  test.describe("Affichage de l'iframe carte", () => {
    test("L'iframe de la carte s'affiche correctement (screenshot)", async ({
      page,
    }) => {
      await page.goto(`/lookbook/preview/iframe/carte/`, {
        waitUntil: "domcontentloaded",
      })

      await page.waitForTimeout(2000)

      await expect(page).toHaveScreenshot("iframe-carte.png", { timeout: 10000 })
    })
  })

  test.describe("Configuration de l'iframe assistant", () => {
    test("L'iframe de l'assistant a les bons attributs (géolocalisation)", async ({
      page,
    }) => {
      test.slow()
      await page.goto(`/lookbook/preview/iframe/assistant/`, {
        waitUntil: "domcontentloaded",
      })

      const iframe = page.locator("iframe#assistant")

      await expect(iframe).toHaveAttribute("allow", /geolocation/)
    })
  })

  test.describe("Rétrocompatibilité des URLs d'iframe", () => {
    test("Les anciennes URLs d'iframe fonctionnent toujours", async ({ page }) => {
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

  test.describe("Persistance du mode iframe", () => {
    test("Le mode iframe persiste lors de la navigation entre pages", async ({
      page,
      baseURL,
    }) => {
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

  test.describe("Tracking du referrer dans les iframes", () => {
    test("Le referrer parent est correctement tracké lors des clics sur des liens dans l'iframe", async ({
      page,
    }) => {
      // Navigate to the test page
      await page.goto("/lookbook/preview/tests/t_1_referrer", {
        waitUntil: "domcontentloaded",
      })

      // Get the parent window location for comparison
      const parentLocation = page.url()

      // Locate the test iframe
      const iframe = page.frameLocator("iframe#test")

      // Wait for iframe to load by waiting for the body with Stimulus controller
      await expect(iframe.locator("body[data-controller*='analytics']")).toBeAttached({
        timeout: 10000,
      })

      // Find a visible link using Playwright's built-in visibility detection
      const visibleLink = iframe.locator("a:visible").first()
      await expect(visibleLink).toBeVisible({ timeout: 10000 })

      // Get the current URL before clicking to detect navigation
      const initialUrl = await iframe
        .locator("body")
        .evaluate(() => window.location.href)

      await visibleLink.click()

      // Wait for navigation by checking that the URL has actually changed
      await expect(async () => {
        const currentUrl = await iframe
          .locator("body")
          .evaluate(() => window.location.href)
        expect(currentUrl).not.toBe(initialUrl)
      }).toPass({ timeout: 10000 })

      // Wait for the analytics controller to be available after navigation
      await expect(async () => {
        const hasController = await iframe.locator("body").evaluate(() => {
          return !!(window as any).stimulus?.getControllerForElementAndIdentifier(
            document.querySelector("body"),
            "analytics",
          )
        })
        expect(hasController).toBe(true)
      }).toPass({ timeout: 5000 })

      // Execute JavaScript inside the iframe to get personProperties
      // This can seem a bit cumbersome, but is the result of quite a lot of trial
      // and error.
      // Playwright does not play well with iframes...
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
test.describe("📜 Accessibilité des Scripts d'Intégration", () => {
  /**
   * Tests for embed script routes
   *
   * These tests verify that all embed script files are accessible
   * and return the correct content type using HTTP fetch.
   */

  test("Le script carte.js est accessible avec le bon content-type", async ({
    page,
  }) => {
    const response = await page.goto("/static/carte.js")
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("Le script iframe.js est accessible avec le bon content-type", async ({
    page,
  }) => {
    const response = await page.goto("/static/iframe.js")
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("Le script infotri.js est accessible avec le bon content-type", async ({
    page,
  }) => {
    const response = await page.goto("/iframe.js")
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("Le script configurateur.js est accessible avec le bon content-type", async ({
    page,
  }) => {
    const response = await page.goto("/infotri/configurateur.js")
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })
})
