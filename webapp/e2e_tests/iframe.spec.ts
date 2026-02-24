import { expect } from "@playwright/test"
import { test } from "./fixtures"
import { navigateTo, getIframe, TIMEOUT } from "./helpers"

test.describe("📦 Système d'Intégration Iframe", () => {
  test.describe("Génération des iframes avec ID corrects", () => {
    test("L'iframe de la carte a l'ID 'carte'", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/iframe/carte")

      const iframe = page.locator("iframe#carte")
      await expect(iframe).toBeAttached({ timeout: TIMEOUT.DEFAULT })
    })

    test("L'iframe du formulaire a l'ID 'formulaire'", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/iframe/formulaire")

      const iframe = page.locator("iframe#formulaire")
      await expect(iframe).toBeAttached({ timeout: TIMEOUT.DEFAULT })
    })

    test("L'iframe de l'assistant a l'ID 'assistant'", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/iframe/assistant")

      const iframe = page.locator("iframe#assistant")
      await expect(iframe).toBeAttached({ timeout: TIMEOUT.DEFAULT })
    })

    test("L'iframe du configurateur infotri a l'ID 'infotri-configurator'", async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/iframe/infotri_configurator")

      const iframe = page.locator("iframe#infotri-configurator")
      await expect(iframe).toBeAttached()
    })

    test("L'iframe infotri a l'ID 'infotri'", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/iframe/infotri")

      const iframe = page.locator("iframe#infotri")
      await expect(iframe).toBeAttached()
    })
  })

  test.describe("Configuration de l'iframe formulaire", () => {
    test("L'iframe est chargée avec les bons paramètres et attributs", async ({
      page,
      baseURL,
    }) => {
      await navigateTo(page, `/lookbook/preview/iframe/formulaire/`)

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
      // The ref parameter is base64-encoded referrer URL, which depends on the environment
      const expectedReferrer = `${baseURL}/lookbook/preview/iframe/formulaire/`
      const expectedRef = Buffer.from(expectedReferrer).toString("base64")
      expect(src).toBe(
        `${baseURL}/formulaire?ref=${encodeURIComponent(expectedRef)}&direction=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
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
      await navigateTo(page, `/lookbook/preview/iframe/formulaire/`)

      const iframeElement = getIframe(page, "formulaire")

      const form = iframeElement.locator("#search_form")
      await expect(form).toBeVisible({ timeout: TIMEOUT.DEFAULT })

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
      await navigateTo(page, `/lookbook/preview/iframe/carte/`)

      await page.waitForTimeout(2000)

      await expect(page).toHaveScreenshot("iframe-carte.png", {
        timeout: TIMEOUT.DEFAULT,
      })
    })
  })

  test.describe("Configuration de l'iframe assistant", () => {
    test("L'iframe de l'assistant a les bons attributs (géolocalisation)", async ({
      page,
    }) => {
      test.slow()
      await navigateTo(page, `/lookbook/preview/iframe/assistant/`)

      const iframe = page.locator("iframe#assistant")

      await expect(iframe).toHaveAttribute("allow", /geolocation/)
    })
  })

  test.describe("Rétrocompatibilité des URLs d'iframe", () => {
    test("Les anciennes URLs d'iframe fonctionnent toujours", async ({ page }) => {
      await navigateTo(
        page,
        `/formulaire?direction=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
      )
      await expect(page).toHaveURL(
        `/formulaire?direction=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
      )
      await navigateTo(
        page,
        `/carte?action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50`,
      )
      await expect(page).toHaveURL(
        `/carte?action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50`,
      )
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
