import { test, expect } from "@playwright/test"
import { navigateTo, switchToListeMode } from "./helpers"

/**
 * E2E tests for the RGAA audit fixes (contre-audit accessibilité, carte).
 * Each describe block maps to one Notion "Suivi des tâches" card.
 */
test.describe("♿ RGAA", () => {
  test.describe("[Carte] 9.1 — Niveau de titre des sections de la fiche acteur", () => {
    test("Les titres « Adresse » et « Services disponibles » sont des <h4>", async ({
      page,
    }) => {
      await navigateTo(
        page,
        "/lookbook/preview/accessibilite/A11Y_14_acteur_section_heading_level/",
      )
      const headings = page.locator("h4")
      await expect(headings.filter({ hasText: "Adresse" })).toBeAttached()
      await expect(headings.filter({ hasText: "Services disponibles" })).toBeAttached()
      await expect(page.locator("h3", { hasText: "Adresse" })).toHaveCount(0)
    })
  })
  test.describe("[Carte] 7.2 / 12.8 / 12.11 — Tooltip de partage nettoyé", () => {
    test('Le tooltip de partage n\'a pas de tabindex positif, ni role="toolbar", ni aria-describedby', async ({
      page,
    }) => {
      await navigateTo(
        page,
        "/lookbook/preview/accessibilite/share_tooltip_acteur_sans_tabindex/",
      )
      const shareButton = page.locator('button:has(span:text("partager"))')
      await expect(shareButton).not.toHaveAttribute("aria-describedby", /.+/)

      const tooltip = page.locator(".fr-tooltip")
      await expect(tooltip).not.toHaveAttribute("tabindex", "1")

      const shareToolbar = page.locator(".fr-share")
      await expect(shareToolbar).not.toHaveAttribute("role", "toolbar")
    })
  })
  test.describe("[Carte] 5.4 / 5.6 — Titre et en-têtes du tableau mode liste", () => {
    test("Le tableau a une légende (<caption>) non vide", async ({ page }) => {
      await navigateTo(
        page,
        "/lookbook/preview/accessibilite/A11Y_15_mode_liste_table_caption_et_entetes/",
      )
      const caption = page.locator("table caption")
      await expect(caption).toBeAttached()
      await expect(caption).not.toHaveText("")
    })

    test("La colonne « Voir la fiche » a un en-tête non vide", async ({ page }) => {
      await navigateTo(
        page,
        "/lookbook/preview/accessibilite/A11Y_15_mode_liste_table_caption_et_entetes/",
      )
      const headers = page.locator("table thead th")
      await expect(headers).toHaveCount(4)
      const lastHeader = headers.last()
      await expect(lastHeader).not.toHaveText("")
    })
  })
  test.describe("[Site Que faire] 12.7 — Lien d'évitement fonctionnel (bug Firefox)", () => {
    for (const path of ["/", "/carte"]) {
      test(`Le <main id="content"> de ${path} porte tabindex="-1"`, async ({
        page,
      }) => {
        await navigateTo(page, path)
        const main = page.locator("main#content")
        await expect(main).toHaveAttribute("tabindex", "-1")
      })
    }

    test('Le <nav id="fr-navigation"> porte tabindex="-1" quand il est rendu', async ({
      page,
    }) => {
      await navigateTo(page, "/")
      const nav = page.locator("nav#fr-navigation")
      const count = await nav.count()
      if (count > 0) {
        await expect(nav).toHaveAttribute("tabindex", "-1")
      }
    })
  })
  test.describe("[Carte] 8.6 — Titre de page pertinent", () => {
    test("La page carte a un titre mentionnant « carte interactive »", async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      await expect(page).toHaveTitle(/carte interactive/i)
    })
  })
  test.describe("[Site Que faire] 6.1 — Lien info-tri explicite", () => {
    test("Le title du lien info-tri reprend son intitulé visible", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/pages/produit/")
      const link = page.getByTestId("infotri-link")
      await expect(link).toBeVisible()
      const text = (await link.textContent())?.trim()
      const title = await link.getAttribute("title")
      expect(title).toBe(`${text} - Nouvelle fenêtre`)
    })
  })
  test.describe("[Carte] 6.1 — Liens explicites (ajouter un lieu)", () => {
    test('Le bouton "ajouter un lieu" a un aria-label cohérent avec son texte visible', async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/carte/ajouter_un_lieu/")
      const link = page.locator("a").first()
      const text = (await link.textContent())?.trim()
      const ariaLabel = await link.getAttribute("aria-label")
      expect(ariaLabel).toBe(`${text} - Nouvelle fenêtre`)
    })
    // Le title des liens de partage (Facebook, X, LinkedIn, email) est
    // couvert par integration_tests/core/test_sharer.py, la preview
    // Lookbook du tooltip de partage n'ayant pas de request.resolver_match
    // pour générer le sharer réel.
  })
  test.describe("[Carte] 8.9 — Balise sémantique pour la date de mise à jour", () => {
    test("La date de mise à jour de la fiche acteur est dans une balise <p>", async ({
      page,
    }) => {
      await navigateTo(page, "/lookbook/preview/pages/acteur/")
      const updatedDate = page.locator("p", { hasText: "Mis à jour le" })
      await expect(updatedDate).toBeVisible()
    })
  })
  test.describe("[Carte] 10.8 — Alternative textuelle pour l'illustration mode liste vide", () => {
    test("Le mode liste sans résultat a une alternative textuelle pour les technologies d'assistance", async ({
      page,
    }) => {
      // Bounding box en pleine mer : garantit l'absence de résultat.
      await navigateTo(
        page,
        '/carte?bounding_box={"southWest":{"lat":0,"lng":0},"northEast":{"lat":1,"lng":1}}',
      )
      await switchToListeMode(page)
      const alt = page.getByText("Aucun résultat trouvé pour votre recherche.")
      await expect(alt).toBeAttached()
    })
  })
  test.describe("[Site Que faire] 1.2 — Image info-tri décorative ignorée", () => {
    test("L'image info-tri a un alt vide", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/pages/produit/")
      const infotriImg = page.locator(".qf-h-\\[80px\\] img")
      await expect(infotriImg.first()).toHaveAttribute("alt", "")
    })
  })
  test.describe("[Carte] 1.2 — Logo décoratif dans les onglets Labels/Sources", () => {
    test("Le logo précédant un label/source a un alt vide", async ({ page }) => {
      await navigateTo(page, "/lookbook/preview/pages/acteur/")
      const logoImg = page.locator('img[src*="/media/logos/"], img[src*="/logos/"]')
      const count = await logoImg.count()
      if (count > 0) {
        await expect(logoImg.first()).toHaveAttribute("alt", "")
      }
    })
  })
  test.describe("[Site Que faire] 6.1 — Lien logo header explicite sur la carte", () => {
    test('Le lien logo du header carte expose un libellé "Accueil — ..."', async ({
      page,
    }) => {
      await navigateTo(page, "/carte")
      const logoLink = page.locator("#logo a[href='/']").first()
      await expect(logoLink).toHaveAccessibleName(/Accueil — /)
    })
  })
})
