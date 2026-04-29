import { AxeBuilder } from "@axe-core/playwright"
import { test, expect, Page } from "@playwright/test"
import { navigateTo } from "./helpers"

test.describe("♿ Conformité Accessibilité WCAG", () => {
  // Shared variables
  const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
  const IFRAME_SELECTOR = "iframe"

  test.describe("Conformité WCAG 2.1 AA des pages principales", () => {
    test("L'iframe du formulaire respecte les critères WCAG 2.1 AA", async ({
      page,
    }) => {
      await navigateTo(page, `/lookbook/preview/iframe/formulaire/`)

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include(IFRAME_SELECTOR) // Restrict scan to the iframe
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })

    test("L'iframe de la carte respecte les critères WCAG 2.1 AA", async ({ page }) => {
      await navigateTo(page, `/lookbook/preview/iframe/carte/`)

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include(IFRAME_SELECTOR) // Restrict scan to the iframe
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })

    test("La page d'accueil de l'assistant respecte les critères WCAG 2.1 AA", async ({
      page,
    }) => {
      // TODO: Update the route for production
      await navigateTo(page, `/`)

      const accessibilityScanResults = await new AxeBuilder({ page })
        .exclude("[data-disable-axe]")
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })

    test("La page de détail produit de l'assistant respecte les critères WCAG 2.1 AA", async ({
      page,
    }) => {
      await navigateTo(page, `/dechet/smartphone`)

      const accessibilityScanResults = await new AxeBuilder({ page })
        .exclude("[data-disable-axe]")
        // ImpactCO2 iframe does not load during e2e tests, it is safe
        // to exclude it usually includes a title and is a valid <iframe>
        // tag.
        .exclude('iframe[src*="impactco2.fr"]')
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })
  })

  test.describe("Vérifications RGAA génériques", () => {
    // -----------------------------------------------------------------------
    // Routes représentatives utilisées pour les contrôles génériques.
    // -----------------------------------------------------------------------
    const ROUTES_PRINCIPALES = [
      "/",
      "/qui-sommes-nous/",
      "/bonus-reparation/",
      "/dechet/smartphone/",
    ] as const

    const ROUTES_SITES_FACILES = ["/qui-sommes-nous/", "/bonus-reparation/"] as const

    const ROUTES_PRODUIT_SANS_FIL_ARIANE = [
      "/categories/meubles/canape/",
      "/dechet/smartphone/",
    ] as const

    // Lien vers le suivi des NCs RGAA encore ouvertes
    const NOTION_BACKLOG_RGAA =
      "https://www.notion.so/Backlog-RGAA-89e89ccdd08d4ac4bc38f7058b67498a"

    // -----------------------------------------------------------------------
    // Petits utilitaires partagés (volontairement locaux à ce describe).
    // -----------------------------------------------------------------------

    /**
     * Récupère la liste ordonnée des niveaux de titres du DOM (ex: [1, 2, 2, 3]).
     */
    async function getHeadingLevels(page: Page): Promise<number[]> {
      return await page.evaluate(() => {
        const headings = Array.from(
          document.querySelectorAll("h1, h2, h3, h4, h5, h6"),
        ) as HTMLElement[]
        return headings
          .filter((h) => {
            // Ignore les titres masqués via aria-hidden, qui ne participent pas
            // à la structure exposée aux technologies d'assistance.
            const ariaHidden = h.closest('[aria-hidden="true"]')
            return ariaHidden === null
          })
          .map((h) => parseInt(h.tagName.substring(1), 10))
      })
    }

    /**
     * Détecte le premier saut de niveau (ex: h1 -> h3 sans h2 intermédiaire).
     * Retourne null si l'enchaînement est correct.
     */
    function findHeadingSkip(levels: number[]): { from: number; to: number } | null {
      for (let i = 1; i < levels.length; i++) {
        const previous = levels[i - 1]
        const current = levels[i]
        // On peut redescendre de plusieurs niveaux, mais on ne peut monter
        // que d'un seul niveau à la fois.
        if (current > previous + 1) {
          return { from: previous, to: current }
        }
      }
      return null
    }

    // -----------------------------------------------------------------------
    // 1. Liens d'évitement (RGAA 12.7)
    // -----------------------------------------------------------------------
    for (const route of ROUTES_PRINCIPALES) {
      test(`Liens d'évitement présents sur ${route} (RGAA 12.7)`, async ({ page }) => {
        await navigateTo(page, route)
        const skipLink = page.locator(
          'nav[aria-label="Accès rapide"] a[href="#content"]',
        )
        await expect(skipLink).toBeAttached()
      })
    }

    // -----------------------------------------------------------------------
    // 2. Landmarks ARIA (RGAA 12.6)
    // -----------------------------------------------------------------------
    for (const route of ROUTES_PRINCIPALES) {
      test(`Landmarks ARIA présents sur ${route} (RGAA 12.6)`, async ({ page }) => {
        await navigateTo(page, route)

        // Exactement un banner
        const banners = page.locator('[role="banner"], header[role="banner"]')
        await expect(banners).toHaveCount(1)

        // Exactement un main (role="main" ou <main>)
        const mains = page.locator('main, [role="main"]')
        await expect(mains).toHaveCount(1)

        // Au moins un <nav> avec un aria-label non vide
        const navsWithLabel = page.locator("nav[aria-label]")
        const labelledNavCount = await navsWithLabel.count()
        expect(labelledNavCount).toBeGreaterThan(0)

        // Vérifie qu'au moins un nav a un aria-label réellement renseigné
        const labels = await navsWithLabel.evaluateAll((nodes) =>
          nodes.map((n) => (n.getAttribute("aria-label") ?? "").trim()),
        )
        expect(labels.some((label) => label.length > 0)).toBe(true)
      })
    }

    // -----------------------------------------------------------------------
    // 3. Pied de page : au moins un <nav> (RGAA 9.2)
    //    NC connue : actuellement aucun <nav> dans le footer en production.
    //    Test marqué `test.fail()` pour suivre la régression sans bloquer la CI.
    //    Voir [Backlog RGAA Notion](https://www.notion.so/Backlog-RGAA-89e89ccdd08d4ac4bc38f7058b67498a)
    // -----------------------------------------------------------------------
    test.fail(
      "Le pied de page contient au moins un <nav> (RGAA 9.2)",
      async ({ page }) => {
        // NC connue : le footer DSFR n'expose pas encore de landmark <nav>.
        // Lien : https://www.notion.so/Backlog-RGAA-89e89ccdd08d4ac4bc38f7058b67498a
        // Le test passera quand le footer aura été corrigé.
        expect(NOTION_BACKLOG_RGAA).toBeTruthy()
        await navigateTo(page, "/")
        const footerNav = page.locator("footer nav")
        await expect(footerNav.first()).toBeAttached()
      },
    )

    // -----------------------------------------------------------------------
    // 4. Fil d'Ariane (RGAA 7.1, 7.3, 12.2)
    // -----------------------------------------------------------------------
    for (const route of ROUTES_SITES_FACILES) {
      test(`Fil d'Ariane présent et correct sur ${route} (RGAA 7.1, 7.3, 12.2)`, async ({
        page,
      }) => {
        await navigateTo(page, route)

        const breadcrumb = page
          .locator('.fr-breadcrumb, nav[aria-label*="riane" i]')
          .first()
        await expect(breadcrumb).toBeAttached()

        // Vérifie que le dernier item est :
        //  - soit un <a> avec un href non nul
        //  - soit marqué [aria-current="page"] et focusable (tabindex >= 0)
        // ET qu'il porte aria-current="page"
        const lastItemInfo = await breadcrumb.evaluate((node) => {
          const items = Array.from(
            node.querySelectorAll("li, .fr-breadcrumb__item"),
          ) as HTMLElement[]
          if (items.length === 0) return null
          const last = items[items.length - 1]
          const link = last.querySelector("a") as HTMLAnchorElement | null
          const ariaCurrent =
            last.getAttribute("aria-current") ??
            link?.getAttribute("aria-current") ??
            null
          const href = link?.getAttribute("href") ?? null
          const tabindexRaw =
            last.getAttribute("tabindex") ?? link?.getAttribute("tabindex") ?? null
          const tabindex = tabindexRaw === null ? null : parseInt(tabindexRaw, 10)
          return { hasLink: !!link, href, ariaCurrent, tabindex }
        })

        expect(lastItemInfo).not.toBeNull()
        expect(lastItemInfo!.ariaCurrent).toBe("page")

        const isReachableViaLink =
          lastItemInfo!.hasLink &&
          lastItemInfo!.href !== null &&
          lastItemInfo!.href.length > 0
        const isReachableViaTabindex =
          lastItemInfo!.tabindex === null || lastItemInfo!.tabindex >= 0
        expect(isReachableViaLink || isReachableViaTabindex).toBe(true)
      })
    }

    // -----------------------------------------------------------------------
    // 4 bis. Fil d'Ariane manquant sur les pages produit (RGAA 12.2)
    //        NC connue : ces gabarits n'embarquent pas encore de fil d'Ariane.
    //        Voir [Backlog RGAA Notion](https://www.notion.so/Backlog-RGAA-89e89ccdd08d4ac4bc38f7058b67498a)
    // -----------------------------------------------------------------------
    for (const route of ROUTES_PRODUIT_SANS_FIL_ARIANE) {
      test.fail(
        `Fil d'Ariane présent sur ${route} (RGAA 12.2)`,
        async ({ page }) => {
          // NC connue : les gabarits produit (nouveau et ancien) ne contiennent
          // pas de fil d'Ariane. Le test échoue volontairement tant que la NC
          // n'est pas corrigée.
          // Suivi : https://www.notion.so/Backlog-RGAA-89e89ccdd08d4ac4bc38f7058b67498a
          await navigateTo(page, route)
          const breadcrumb = page.locator(
            '.fr-breadcrumb, nav[aria-label*="riane" i]',
          )
          await expect(breadcrumb.first()).toBeAttached()
        },
      )
    }

    // -----------------------------------------------------------------------
    // 5. Hiérarchie des titres (RGAA 9.1)
    // -----------------------------------------------------------------------
    for (const route of ROUTES_PRINCIPALES) {
      test(`Hiérarchie des titres correcte sur ${route} (RGAA 9.1)`, async ({
        page,
      }) => {
        await navigateTo(page, route)

        // Exactement un <h1>
        const h1Count = await page.locator("h1").count()
        expect(h1Count, `${route} doit contenir exactement un <h1>`).toBe(1)

        // Pas de saut de niveau dans la hiérarchie des titres
        const levels = await getHeadingLevels(page)
        const skip = findHeadingSkip(levels)
        expect(
          skip,
          `${route} : saut de niveau détecté h${skip?.from} -> h${skip?.to} (séquence ${levels.join(",")})`,
        ).toBeNull()
      })
    }

    // -----------------------------------------------------------------------
    // 6. Alternatives textuelles des images et SVG (RGAA 1.1)
    // -----------------------------------------------------------------------
    for (const route of ROUTES_PRINCIPALES) {
      test(`Toutes les images et SVG ont une alternative textuelle sur ${route} (RGAA 1.1)`, async ({
        page,
      }) => {
        await navigateTo(page, route)

        const imagesSansAlternative = await page.evaluate(() => {
          const offenders: string[] = []
          const imgs = Array.from(document.querySelectorAll("img")) as HTMLImageElement[]
          for (const img of imgs) {
            const alt = img.getAttribute("alt")
            const ariaHidden = img.getAttribute("aria-hidden") === "true"
            // alt="" est valide (image décorative). alt absent ne l'est pas.
            const hasAlt = alt !== null
            if (!hasAlt && !ariaHidden) {
              offenders.push(`<img src="${img.getAttribute("src") ?? ""}">`)
            }
          }
          return offenders
        })
        expect(
          imagesSansAlternative,
          `Images sans alt ni aria-hidden : ${imagesSansAlternative.join(", ")}`,
        ).toEqual([])

        const svgsSansAlternative = await page.evaluate(() => {
          const offenders: string[] = []
          const svgs = Array.from(document.querySelectorAll("svg")) as SVGElement[]
          for (const svg of svgs) {
            const ariaHidden = svg.getAttribute("aria-hidden") === "true"
            const ariaLabel = (svg.getAttribute("aria-label") ?? "").trim()
            const ariaLabelledby = (
              svg.getAttribute("aria-labelledby") ?? ""
            ).trim()
            const hasTitle = svg.querySelector("title") !== null
            const hasRolePresentation =
              svg.getAttribute("role") === "presentation" ||
              svg.getAttribute("role") === "none"
            if (
              !ariaHidden &&
              !ariaLabel &&
              !ariaLabelledby &&
              !hasTitle &&
              !hasRolePresentation
            ) {
              const cls = svg.getAttribute("class") ?? ""
              offenders.push(`<svg class="${cls}">`)
            }
          }
          return offenders
        })
        expect(
          svgsSansAlternative,
          `SVG sans alternative : ${svgsSansAlternative.join(", ")}`,
        ).toEqual([])
      })
    }

    // -----------------------------------------------------------------------
    // 7. Pas de tabindex="-1" sur <a>/<button> dans une boîte de dialogue
    //    (RGAA 7.3 / 12.7) : garde-fou de non-régression.
    // -----------------------------------------------------------------------
    for (const route of ROUTES_PRINCIPALES) {
      test(`Aucun <a>/<button> avec tabindex="-1" dans un dialog sur ${route} (RGAA 7.3)`, async ({
        page,
      }) => {
        await navigateTo(page, route)

        const offenders = await page.evaluate(() => {
          const dialogs = Array.from(
            document.querySelectorAll('dialog, [role="dialog"]'),
          )
          const out: string[] = []
          for (const dlg of dialogs) {
            const focusables = Array.from(
              dlg.querySelectorAll('a[tabindex="-1"], button[tabindex="-1"]'),
            )
            for (const node of focusables) {
              out.push(`${node.tagName.toLowerCase()} dans ${dlg.tagName.toLowerCase()}`)
            }
          }
          return out
        })
        expect(offenders, `Éléments fautifs : ${offenders.join(", ")}`).toEqual([])
      })
    }

    // -----------------------------------------------------------------------
    // 8. Indicateur de focus visible sur les champs de formulaire (RGAA 10.7)
    // -----------------------------------------------------------------------
    test("Indicateur de focus visible sur les champs interactifs de la page d'accueil (RGAA 10.7)", async ({
      page,
    }) => {
      await navigateTo(page, "/")

      const interactiveSelectors =
        'input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled])'
      const handles = await page
        .locator(interactiveSelectors)
        .elementHandles()
      const sample = handles.slice(0, 5)

      // Aucun champ interactif sur la home : on évite un faux positif.
      if (sample.length === 0) {
        test.skip(true, "Aucun champ interactif sur la page d'accueil")
        return
      }

      for (const handle of sample) {
        // Un champ peut être en dehors du viewport (footer) ou non focusable :
        // on tente le focus mais on tolère l'erreur, on vérifie ensuite l'état.
        try {
          await handle.focus()
        } catch {
          continue
        }

        const focusInfo = await handle.evaluate((node) => {
          const el = node as HTMLElement
          const style = window.getComputedStyle(el)
          const outlineWidth = parseFloat(style.outlineWidth || "0")
          const outlineStyle = style.outlineStyle
          const boxShadow = style.boxShadow
          return {
            outlineWidth,
            outlineStyle,
            boxShadow,
            tag: el.tagName.toLowerCase(),
            name: (el as HTMLInputElement).name ?? "",
          }
        })

        const hasOutline =
          focusInfo.outlineStyle !== "none" && focusInfo.outlineWidth > 0
        const hasBoxShadow =
          focusInfo.boxShadow !== "none" && focusInfo.boxShadow.trim().length > 0

        expect(
          hasOutline || hasBoxShadow,
          `Le champ <${focusInfo.tag} name="${focusInfo.name}"> n'a pas d'indicateur de focus visible (outline:${focusInfo.outlineStyle} ${focusInfo.outlineWidth}px, box-shadow:${focusInfo.boxShadow})`,
        ).toBe(true)
      }
    })

    // -----------------------------------------------------------------------
    // 9. Ordre de tabulation : le premier focusable est le lien d'évitement
    //    (RGAA 12.7 fonctionnel)
    // -----------------------------------------------------------------------
    test("Le premier élément focusable est le lien d'évitement \"Contenu\" (RGAA 12.7)", async ({
      page,
    }) => {
      await navigateTo(page, "/")

      // Pose le focus dans le <body> avant de presser Tab pour que le focus
      // démarre bien depuis le tout début du document.
      await page.evaluate(() => {
        if (document.body) {
          (document.body as HTMLBodyElement).focus()
        }
      })

      await page.keyboard.press("Tab")

      const focused = await page.evaluate(() => {
        const el = document.activeElement as HTMLElement | null
        if (!el) return null
        return {
          tag: el.tagName.toLowerCase(),
          href: el.getAttribute("href"),
          text: (el.textContent ?? "").trim(),
        }
      })
      expect(focused).not.toBeNull()
      expect(focused!.tag).toBe("a")
      expect(focused!.href).toBe("#content")
      expect(focused!.text.toLowerCase()).toContain("contenu")
    })

    // -----------------------------------------------------------------------
    // 10. Titres d'iframes (RGAA 2.2)
    // -----------------------------------------------------------------------
    for (const route of ROUTES_PRINCIPALES) {
      test(`Toutes les iframes ont un title non vide et distinct sur ${route} (RGAA 2.2)`, async ({
        page,
      }) => {
        await navigateTo(page, route)

        const titles = await page.evaluate(() => {
          const iframes = Array.from(document.querySelectorAll("iframe"))
          return iframes.map((f) => (f.getAttribute("title") ?? "").trim())
        })

        // Aucune iframe : pas de NC possible.
        if (titles.length === 0) {
          return
        }

        const empty = titles.filter((t) => t.length === 0)
        expect(empty, `${empty.length} iframe(s) sans title`).toEqual([])

        const seen = new Set<string>()
        const duplicates: string[] = []
        for (const t of titles) {
          if (seen.has(t)) {
            duplicates.push(t)
          }
          seen.add(t)
        }
        expect(
          duplicates,
          `Titres d'iframes en doublon : ${duplicates.join(", ")}`,
        ).toEqual([])
      })
    }

    // -----------------------------------------------------------------------
    // 11. Étiquetage des champs de formulaire (RGAA 11.1)
    // -----------------------------------------------------------------------
    for (const route of ROUTES_PRINCIPALES) {
      test(`Tous les champs de formulaire ont un libellé sur ${route} (RGAA 11.1)`, async ({
        page,
      }) => {
        await navigateTo(page, route)

        const offenders = await page.evaluate(() => {
          const fields = Array.from(
            document.querySelectorAll("input, select, textarea"),
          ) as (HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement)[]
          const ignoredTypes = new Set([
            "hidden",
            "button",
            "submit",
            "reset",
            "image",
          ])
          const out: string[] = []
          for (const field of fields) {
            const type = (field.getAttribute("type") ?? "").toLowerCase()
            if (ignoredTypes.has(type)) continue

            const id = field.getAttribute("id")
            const ariaLabel = (field.getAttribute("aria-label") ?? "").trim()
            const ariaLabelledby = (
              field.getAttribute("aria-labelledby") ?? ""
            ).trim()

            // <label> associé via for=id
            let labelled = false
            if (id) {
              const escapedId = (window as any).CSS?.escape
                ? (window as any).CSS.escape(id)
                : id.replace(/"/g, '\\"')
              if (document.querySelector(`label[for="${escapedId}"]`)) {
                labelled = true
              }
            }
            // <label> englobant
            if (!labelled && field.closest("label")) {
              labelled = true
            }
            // aria-label
            if (!labelled && ariaLabel.length > 0) {
              labelled = true
            }
            // aria-labelledby pointant vers un élément existant
            if (!labelled && ariaLabelledby.length > 0) {
              const ids = ariaLabelledby.split(/\s+/).filter(Boolean)
              const allFound = ids.every((refId) =>
                document.getElementById(refId) !== null,
              )
              if (allFound) labelled = true
            }
            // <fieldset><legend> (cas des radios/checkbox groupées)
            if (!labelled && (type === "radio" || type === "checkbox")) {
              const fs = field.closest("fieldset")
              if (fs && fs.querySelector("legend")) {
                labelled = true
              }
            }

            if (!labelled) {
              out.push(
                `<${field.tagName.toLowerCase()} type="${type}" name="${field.getAttribute("name") ?? ""}" id="${id ?? ""}">`,
              )
            }
          }
          return out
        })

        expect(
          offenders,
          `Champs sans libellé accessible : ${offenders.join(" | ")}`,
        ).toEqual([])
      })
    }

    // -----------------------------------------------------------------------
    // 12. Liens externes : indication "nouvelle fenêtre" (RGAA 13.x / 10.2)
    // -----------------------------------------------------------------------
    for (const route of ROUTES_PRINCIPALES) {
      test(`Les liens target=_blank indiquent une nouvelle fenêtre sur ${route} (RGAA 13.x)`, async ({
        page,
      }) => {
        await navigateTo(page, route)

        const offenders = await page.evaluate(() => {
          const out: string[] = []
          const anchors = Array.from(
            document.querySelectorAll('a[target="_blank"]'),
          ) as HTMLAnchorElement[]
          for (const a of anchors) {
            // On agrège le texte visible + aria-label + title, en français.
            const visible = (a.textContent ?? "").toLowerCase()
            const ariaLabel = (a.getAttribute("aria-label") ?? "").toLowerCase()
            const title = (a.getAttribute("title") ?? "").toLowerCase()
            const haystack = `${visible} ${ariaLabel} ${title}`
            if (!haystack.includes("nouvelle fenêtre")) {
              out.push(a.getAttribute("href") ?? "(no href)")
            }
          }
          return out
        })

        expect(
          offenders,
          `Liens externes sans mention "nouvelle fenêtre" : ${offenders.join(", ")}`,
        ).toEqual([])
      })
    }

    // -----------------------------------------------------------------------
    // 13. Sweep axe sur le nouveau gabarit produit (post-audit mai 2025)
    // -----------------------------------------------------------------------
    test("Le nouveau gabarit produit /categories/meubles/canape/ respecte WCAG 2.1 AA", async ({
      page,
    }) => {
      await navigateTo(page, "/categories/meubles/canape/")

      const accessibilityScanResults = await new AxeBuilder({ page })
        .exclude("[data-disable-axe]")
        .exclude('iframe[src*="impactco2.fr"]')
        .withTags(WCAG_TAGS)
        .analyze()

      expect(accessibilityScanResults.violations).toEqual([])
    })

    // -----------------------------------------------------------------------
    // 14. Sweep axe sur les pages Sites Faciles les plus visitées
    // -----------------------------------------------------------------------
    for (const route of ROUTES_SITES_FACILES) {
      test(`La page Sites Faciles ${route} respecte WCAG 2.1 AA`, async ({
        page,
      }) => {
        await navigateTo(page, route)

        const accessibilityScanResults = await new AxeBuilder({ page })
          .exclude("[data-disable-axe]")
          .exclude('iframe[src*="impactco2.fr"]')
          .exclude('iframe[src*="youtube.com"]')
          .exclude('iframe[src*="youtube-nocookie.com"]')
          .withTags(WCAG_TAGS)
          .analyze()

        expect(accessibilityScanResults.violations).toEqual([])
      })
    }
  })
})
