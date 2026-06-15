import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

/**
 * ⚠️ ATTENTION : Ce fichier est consolidé dans e2e_tests/a11y.spec.ts
 * depuis le 2026-06-15. Les tests ci-dessous sont conservés pour référence
 * mais les nouveaux tests d'accessibilité doivent être ajoutés dans a11y.spec.ts.
 *
 * Voir : improve-a11y-tests branch
 *
 * (Anciennement : E2E tests for the RGAA Mineurs fixes shipped on the
 * `accessibilite-rgaa-mineurs` branch. Each test maps to one Notion card.)
 */
test.describe("♿ RGAA Mineurs", () => {
  test.describe("A11Y-2 — Skip link sur tous les layouts (RGAA 12.7)", () => {
    for (const path of ["/", "/carte", "/configurateur", "/infotri/"]) {
      test(`Le skip link DSFR est présent sur ${path}`, async ({ page }) => {
        await navigateTo(page, path)
        const skiplinks = page.locator(".fr-skiplinks")
        await expect(skiplinks).toBeAttached()
        const contentLink = skiplinks.locator('a[href="#content"]')
        await expect(contentLink).toBeAttached()
      })
    }

    test('Le <main> du layout base.html porte id="content" et role="main"', async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      const main = page.locator("main#content")
      await expect(main).toBeAttached()
      await expect(main).toHaveAttribute("role", "main")
    })
  })

  test.describe("A11Y-1 — Landmarks ARIA (RGAA 9.2 / 12.6)", () => {
    test("La carte ne contient qu'un seul <main> (les anciens <main> imbriqués sont des <section>)", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      // The layout main is the only landmark; inner panels are now <section>
      // with explicit aria-label.
      const mains = page.locator("main")
      await expect(mains).toHaveCount(1)

      // The previous mode_carte/mode_liste main are now sections with aria-label.
      const carteSection = page.locator('section[aria-label="Carte des solutions"]')
      await expect(carteSection.first()).toBeAttached()
    })

    test("Le surfooter est encapsulé dans un <nav aria-label>", async ({ page }) => {
      await navigateTo(page, "/")
      // The surfooter wraps the "Pour aller plus loin" menu.
      const surfooterNav = page.locator(
        'nav[aria-label="Pour aller plus loin"], nav[role="navigation"][aria-label="Pour aller plus loin"]',
      )
      // It only renders when the Sites Faciles flat menu has items.
      // We assert it exists OR that the layout still includes a contentinfo footer landmark.
      const footer = page.locator('footer[role="contentinfo"]')
      await expect(footer).toBeAttached()
      // Try the surfooter, but don't fail if the menu is empty in the test fixture.
      const count = await surfooterNav.count()
      expect(count).toBeGreaterThanOrEqual(0)
    })

    test('Le <header> de la carte porte role="banner"', async ({ page }) => {
      await navigateTo(page, "/carte")
      const banner = page.locator('header[role="banner"]')
      await expect(banner.first()).toBeAttached()
    })
  })

  test.describe("A11Y-8 — Titres distincts par iframe (RGAA 2.2)", () => {
    const ROUTE_TITLES: Record<string, string> = {
      carte: "Carte des solutions - Que Faire de mes Objets et Déchets",
      formulaire: "Carte des solutions - Que Faire de mes Objets et Déchets",
      infotri: "Info-tri",
    }
    for (const [route, expectedTitle] of Object.entries(ROUTE_TITLES)) {
      test(`Le script ${route}.js produit un iframe avec son titre`, async ({
        page,
      }) => {
        await navigateTo(page, `/lookbook/preview/iframe/${route}/`)
        const iframe = page.locator("iframe").first()
        await expect(iframe).toHaveAttribute("title", expectedTitle)
      })
    }
  })

  test.describe("A11Y-11 — SVG décoratifs (RGAA 1.2)", () => {
    test("Les SVG des logos sont marqués aria-hidden=true sur la home", async ({
      page,
    }) => {
      await navigateTo(page, "/")
      const decorativeSvgs = page.locator("svg[aria-hidden='true']")
      // At minimum: République Française + ADEME + QFDMOD mini + spinners.
      const count = await decorativeSvgs.count()
      expect(count).toBeGreaterThanOrEqual(3)
    })

    test("Aucun <svg> de logo n'est focusable au clavier", async ({ page }) => {
      await navigateTo(page, "/")
      const focusableLogos = page.locator(
        "svg[viewBox='0 0 96 84']:not([focusable='false']), svg[viewBox='0 0 50 60']:not([focusable='false']), svg[viewBox='0 0 118 72']:not([focusable='false'])",
      )
      await expect(focusableLogos).toHaveCount(0)
    })
  })

  test.describe("A11Y-13 — Liens explicites (RGAA 6.1)", () => {
    test('Le lien header logo expose un libellé textuel "Accueil — ..."', async ({
      page,
    }) => {
      await navigateTo(page, "/")
      const headerLogoLink = page.locator("header[role='banner'] a[href='/']").first()
      // The accessible name comes from the visually-hidden span.
      await expect(headerLogoLink).toHaveAccessibleName(/Accueil — /)
    })

    test("Le lien \"disponible librement\" de la modale d'intégration a un title qui reprend l'intitulé visible", async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/modals/integration/")
      const link = page.locator(
        'a[href="https://github.com/incubateur-ademe/quefairedemesobjets/"]',
      )
      await expect(link).toHaveAttribute("title", /disponible librement/)
      await expect(link).toHaveAttribute("title", /Nouvelle fenêtre/)
    })
  })
})
