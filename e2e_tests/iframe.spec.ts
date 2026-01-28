import { test, expect } from "@playwright/test"
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

  test.describe("Persistance du mode iframe", () => {
    test("Le mode iframe persiste lors de la navigation entre pages", async ({
      page,
      baseURL,
    }) => {
      test.slow()
      await navigateTo(page, `/?iframe`)
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
    const scriptTypes = [
      { name: "carte", scriptType: "carte", iframeId: "carte", iframePath: "/carte" },
      {
        name: "assistant",
        scriptType: "assistant",
        iframeId: "assistant",
        iframePath: "/dechet",
      },
    ]

    for (const { name, scriptType, iframeId, iframePath } of scriptTypes) {
      test(`Le referrer parent avec query string est correctement passé à l'iframe pour ${name}`, async ({
        page,
      }) => {
        // Navigate to the test page with the script_type parameter and additional query params
        // The script_type selects which template to render via django-lookbook form
        const testQueryParams = "test_param=value&another=123"
        const fullUrl = `/lookbook/preview/tests/t_1_referrer?script_type=${scriptType}&${testQueryParams}`
        await navigateTo(page, fullUrl)

        // Get the parent window location for comparison (must include query params)
        const parentLocation = page.url()
        expect(parentLocation).toContain(testQueryParams)

        // Wait for the iframe to be created with the correct ID
        const iframeLocator = page.locator(`iframe#${iframeId}`)
        await expect(iframeLocator).toBeAttached({ timeout: TIMEOUT.DEFAULT })

        // Get the iframe src attribute and verify it contains the ref parameter
        const iframeSrc = await iframeLocator.getAttribute("src")
        expect(iframeSrc).not.toBeNull()
        expect(iframeSrc).toContain(iframePath)
        expect(iframeSrc).toContain("ref=")

        // Decode the ref parameter and verify it matches the parent URL
        const url = new URL(iframeSrc!, "http://localhost")
        const refParam = url.searchParams.get("ref")
        expect(refParam).not.toBeNull()

        // Decode base64 ref parameter
        const decodedRef = Buffer.from(refParam!, "base64").toString("utf-8")

        // Verify the decoded referrer contains the test query params
        expect(decodedRef).toContain(testQueryParams)
      })
    }
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
