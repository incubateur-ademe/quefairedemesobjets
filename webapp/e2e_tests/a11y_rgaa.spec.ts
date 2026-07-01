import { AxeBuilder } from "@axe-core/playwright"
import { test, expect } from "@playwright/test"
import {
  clickFirstClickableActeurMarker,
  mockApiAdresse,
  navigateTo,
  searchCarteAndWaitForActeurs,
  switchToListeMode,
} from "./helpers"

test.describe("♿ RGAA — Critères ciblés", () => {
  test.describe("Critère 1.1 — Alternative textuelle pour images porteuses d'information", () => {
    test("Le logo ADEME a role='img' et un aria-label pertinent", async ({ page }) => {
      await navigateTo(page, "/carte")
      const ademeLogo = page.locator(
        'svg[aria-label="ADEME - Agence de la transition écologique"]',
      )
      await expect(ademeLogo.first()).toBeAttached()
      await expect(ademeLogo.first()).toHaveAttribute("role", "img")
    })

    test("Le SVG empty-state du mode liste a un role='img' et aria-label", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      const emptySvg = page.locator(
        'svg[aria-label="Aucun résultat trouvé — illustration d\'une épingle de localisation barrée"]',
      )
      await expect(emptySvg).toBeAttached()
      await expect(emptySvg).toHaveAttribute("role", "img")
    })
  })

  test.describe("Critère 1.2 — Images décoratives ignorées", () => {
    test("Le logo Répar'Acteurs dans les filtres a alt='' (décoratif)", async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/filtres/reparacteurs/")
      const reparImg = page.locator('img[alt=""]')
      await expect(reparImg.first()).toBeAttached()
    })

    test("Les logos dans la modale labels/sources ont alt='' (décoratifs)", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)
      await searchCarteAndWaitForActeurs(page, "Auray")
      await clickFirstClickableActeurMarker(page)
      // Navigate to Sources tab
      const sourcesTab = page.getByRole("tab", { name: "Sources" })
      await sourcesTab.click()
      // Check images have alt="" (decorative, doublon with label text)
      const logoImgs = page.locator('#acteurDetailsPanel img[alt=""]')
      await expect(logoImgs.first()).toBeAttached()
    })
  })

  test.describe("Critère 5.4 / 5.6 — Tableau mode liste", () => {
    test("Le tableau du mode liste a une <caption> pertinente", async ({ page }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)
      await searchCarteAndWaitForActeurs(page, "Auray")
      await switchToListeMode(page)
      const caption = page.locator("table caption")
      await expect(caption).toContainText("Liste des lieux")
    })

    test("La colonne 'Fiche' a un <th> avec intitulé", async ({ page }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)
      await searchCarteAndWaitForActeurs(page, "Auray")
      await switchToListeMode(page)
      const lastTh = page.locator("table thead th").last()
      await expect(lastTh).toHaveText("Fiche")
    })
  })

  test.describe("Critère 8.6 — Titre de page pertinent", () => {
    test("Le <title> de la carte mentionne 'carte interactive'", async ({ page }) => {
      await navigateTo(page, "/carte")
      await expect(page).toHaveTitle(/carte interactive/)
    })
  })

  test.describe("Critère 9.1 — Niveaux de titres cohérents", () => {
    test("Les sections de l'encart acteur utilisent <h4> (pas <h3>)", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)
      await searchCarteAndWaitForActeurs(page, "Auray")
      await clickFirstClickableActeurMarker(page)
      const aboutPanel = page.getByTestId("acteur-detail-about-panel")
      await expect(aboutPanel).toBeVisible()
      // The section headings inside the panel should use h4
      const h3InPanel = aboutPanel.locator("h3")
      await expect(h3InPanel).toHaveCount(0)
    })
  })

  test.describe("Critère 9.2 / 12.6 — Structure et Landmarks", () => {
    test("Un seul <main> sur la page carte", async ({ page }) => {
      await navigateTo(page, "/carte")
      const mains = page.locator("main")
      await expect(mains).toHaveCount(1)
    })

    test("Pas de role='banner' à l'intérieur de <main>", async ({ page }) => {
      await navigateTo(page, "/carte")
      const bannerInsideMain = page.locator('main [role="banner"]')
      await expect(bannerInsideMain).toHaveCount(0)
    })

    test("Le header carte a un aria-label descriptif", async ({ page }) => {
      await navigateTo(page, "/carte")
      const carteHeader = page.locator(
        'main header[aria-label="Recherche sur la carte"]',
      )
      await expect(carteHeader.first()).toBeAttached()
    })

    test("Pas de tabpanel orphelin quand l'acteur n'a pas de labels", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      await mockApiAdresse(page)
      await searchCarteAndWaitForActeurs(page, "Auray")
      const marker = clickFirstClickableActeurMarker(page)
      const labelsTab = page.locator('button[role="tab"]', { hasText: "Labels" })
      // Count must match: no tabpanel without corresponding tab
      const tabCount = await labelsTab.count()
      const panelCount = await page
        .locator('[role="tabpanel"]')
        .filter({ has: page.locator("#carte-labelsPanel") })
        .count()
      expect(panelCount).toBe(tabCount)
    })
  })

  test.describe("Critère 11.2 / 11.7 — Étiquettes de formulaire", () => {
    test("Les champs facultatifs affichent '(facultatif)' pas '(Optional)'", async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/modals/filtres/")
      const frenchOptional = page.locator("text=(facultatif)")
      await expect(frenchOptional.first()).toBeAttached()
      const englishOptional = page.locator("text=(Optional)")
      await expect(englishOptional).toHaveCount(0)
    })
  })

  test.describe("Critère 11.6 — Légende des regroupements de champs", () => {
    test("Le groupe radio Carte/Liste a une légende 'Mode d'affichage'", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      const legend = page.locator("legend")
      await expect(legend.filter({ hasText: "Mode d'affichage" })).toBeAttached()
    })
  })

  test.describe("Critère 12.11 — Contenus additionnels atteignables au clavier", () => {
    test("L'ouvreur de la modale Répar'Acteurs est un <button>", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/filtres/reparacteurs/")
      // The Répar'Acteurs icon should now be a <button>
      const openerButton = page.locator("button").filter({
        has: page.locator('img[alt=""]'),
      })
      await expect(openerButton.first()).toBeAttached()
    })
  })

  test.describe("Critère 6.1 — Liens explicites", () => {
    test("Le lien 'Chambre des Métiers' a un title qui reprend l'intitulé visible", async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/filtres/reparacteurs/")
      const cmaLink = page.getByRole("link", {
        name: /Chambre des Métiers/,
      })
      await expect(cmaLink).toHaveAttribute("title", /Chambre des Métiers/)
      await expect(cmaLink).toHaveAttribute("title", /Nouvelle fenêtre/)
    })

    test("Le lien 'Ajouter un lieu' a un aria-label qui reprend l'intitulé visible", async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/iframe/carte/")
      const ajouterLien = page.locator(
        'a[aria-label="Ajouter un lieu sur la carte - Nouvelle fenêtre"]',
      )
      await expect(ajouterLien).toBeAttached()
    })
  })
})

test.describe("♿ Axe-core — Carte interactive après interactions", () => {
  test("La carte avec résultats et mode liste respecte WCAG 2.1 AA", async ({
    page,
  }) => {
    await navigateTo(page, "/carte")
    await mockApiAdresse(page)
    await searchCarteAndWaitForActeurs(page, "Auray")
    await switchToListeMode(page)

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze()
    expect(results.violations).toEqual([])
  })

  test("La carte avec acteur detail ouvert respecte WCAG 2.1 AA", async ({ page }) => {
    await navigateTo(page, "/carte")
    await mockApiAdresse(page)
    await searchCarteAndWaitForActeurs(page, "Auray")
    await clickFirstClickableActeurMarker(page)
    const panel = page.getByTestId("acteur-detail-about-panel")
    await expect(panel).toBeVisible()

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze()
    expect(results.violations).toEqual([])
  })

  test("Les boutons de zoom de la carte ont des titles en français", async ({
    page,
  }) => {
    await navigateTo(page, "/carte")
    const zoomIn = page.getByTitle("Zoom avant")
    const zoomOut = page.getByTitle("Zoom arrière")
    await expect(zoomIn).toBeAttached()
    await expect(zoomOut).toBeAttached()
  })

  test("Le bouton d'attribution de la carte a un title en français", async ({
    page,
  }) => {
    await navigateTo(page, "/carte")
    const attrBtn = page.getByTitle("Afficher les attributions")
    await expect(attrBtn).toBeAttached()
  })
})
