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

  test.describe("Tracking du referrer dans les iframes", () => {
    // TODO: Fix this test - first visible link doesn't navigate, URL stays the same
    test("Le referrer parent est correctement tracké lors des clics sur des liens dans l'iframe", async ({
      page,
    }) => {
      // Navigate to the test page
      await navigateTo(page, "/lookbook/preview/tests/t_1_referrer")

      // Get the parent window location for comparison
      const parentLocation = page.url()

      // Locate the test iframe
      const iframe = getIframe(page, "test")

      // Wait for iframe to load by waiting for the body with Stimulus controller
      await expect(iframe.locator("body[data-controller*='analytics']")).toBeAttached({
        timeout: TIMEOUT.DEFAULT,
      })

      // Find a visible link in the main content area (not in the sidebar)
      // The sidebar links don't trigger navigation, so we need to click on main content links
      const visibleLink = iframe.locator("main a:visible").first()
      await expect(visibleLink).toBeVisible({ timeout: TIMEOUT.DEFAULT })

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
      }).toPass({ timeout: TIMEOUT.DEFAULT })

      // Wait for the analytics controller to be available after navigation
      await expect(async () => {
        const hasController = await iframe.locator("body").evaluate(() => {
          return !!(window as any).stimulus?.getControllerForElementAndIdentifier(
            document.querySelector("body"),
            "analytics",
          )
        })
        expect(hasController).toBe(true)
      }).toPass({ timeout: TIMEOUT.SHORT })

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
  test.describe("🧭 Navigation dans l'iframe avec persistance de l'UI", () => {
    test("L'interface iframe persiste lors de la navigation", async ({ page }) => {
      // Navigate to the test preview page
      await navigateTo(
        page,
        "/lookbook/preview/tests/t_8_iframe_navigation_persistence",
      )

      // Wait for iframe to be created by the integration script
      const iframe = getIframe(page, "assistant")
      await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

      // Helper function to check iframe-specific UI elements
      const checkIframeUI = async () => {
        // Check that header is NOT present (hidden in iframe mode)
        await expect(iframe.locator(".fr-header")).not.toBeVisible()

        // Check that footer is NOT present (hidden in iframe mode)
        await expect(iframe.locator(".fr-footer")).not.toBeVisible()

        // Check that iframe footer link IS present
        await expect(iframe.locator("text=En savoir plus sur ce site")).toBeVisible()
      }

      // Initial page load - verify iframe UI
      await checkIframeUI()

      // Navigate to a product page by clicking search
      const searchInput = iframe.locator('input[name="home-input"]')
      await searchInput.fill("vélo")
      await searchInput.press("Enter")

      // Wait for navigation to complete
      await iframe
        .locator("text=/vélo/i")
        .first()
        .waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })

      // Verify iframe UI persists after search
      await checkIframeUI()

      // Click on a search result
      const firstResult = iframe.locator('[data-testid="suggestion-item"]').first()
      if (await firstResult.isVisible()) {
        await firstResult.click()

        // Wait for product page to load
        await iframe
          .locator("text=/que faire/i")
          .waitFor({ state: "visible", timeout: TIMEOUT.DEFAULT })

        // Verify iframe UI persists on product page
        await checkIframeUI()
      }

      // Navigate back using browser back button if available
      const backButton = iframe.locator("text=/retour/i").first()
      if (await backButton.isVisible()) {
        await backButton.click()

        // Wait for previous page to load
        await iframe
          .locator("body")
          .waitFor({ state: "attached", timeout: TIMEOUT.DEFAULT })

        // Verify iframe UI still persists
        await checkIframeUI()
      }
    })

    test("Les liens internes maintiennent le mode iframe", async ({ page }) => {
      // Navigate to the test preview page
      await navigateTo(
        page,
        "/lookbook/preview/tests/t_8_iframe_navigation_persistence",
      )

      // Wait for iframe to be created
      const iframe = getIframe(page, "assistant")
      await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

      // Search for something - this will show search results inline in a turbo-frame
      const searchInput = iframe.locator('input[name="home-input"]')
      await searchInput.fill("vélo")

      // Wait for search results to appear and click on a visible result
      // The search results appear in the turbo-frame below the search input
      const searchResultsFrame = iframe.locator("turbo-frame#home\\:search-results")
      const firstVisibleResult = searchResultsFrame
        .locator('a[href^="/dechet/"]:visible')
        .first()
      await expect(firstVisibleResult).toBeVisible({ timeout: TIMEOUT.DEFAULT })
      await firstVisibleResult.click()

      // Wait for navigation to product page
      await page.waitForTimeout(500)

      // Verify iframe-specific UI is still present on the product page
      // The standard DSFR footer should not be visible in iframe mode
      await expect(iframe.locator(".fr-footer")).not.toBeVisible()
      // The iframe-specific footer link should be visible
      await expect(iframe.locator("text=En savoir plus sur ce site")).toBeVisible()
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
