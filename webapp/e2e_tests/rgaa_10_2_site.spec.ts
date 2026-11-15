import { test, expect, Page } from "@playwright/test"
import { navigateTo } from "./helpers"

const PAGES = [
  "/categories/biodechets/dechets-alimentaires/",
  "/categories/vetements/",
  "/categories/equipements-electriques-electroniques-deee/telephone-tablette-console/",
]

async function linksOpeningInNewWindowWithoutMention(page: Page) {
  return page.evaluate(() => {
    const collapse = (text: string | null) => (text ?? "").replace(/\s+/g, " ").trim()
    return Array.from(
      document.querySelectorAll<HTMLAnchorElement>('a[target="_blank"]'),
    )
      .filter((link) => {
        if (link.closest("turbo-frame")) return false
        const visibleText = collapse(
          Array.from(link.childNodes)
            .map((node) =>
              node instanceof HTMLElement && node.classList.contains("fr-sr-only")
                ? ""
                : node.textContent,
            )
            .join(" "),
        )
        const hasSrOnlyMention = /nouvelle fenêtre/i.test(
          collapse(link.querySelector(".fr-sr-only")?.textContent),
        )
        const title = collapse(link.getAttribute("title"))
        const hasTitleMention =
          /^(.+) - (ouvre une )?nouvelle fenêtre$/i.test(title) &&
          (link.closest(".fr-share") !== null ||
            title.toLowerCase().startsWith(visibleText.toLowerCase()))
        return !hasSrOnlyMention && !hasTitleMention
      })
      .map((link) => `${collapse(link.textContent)} -> ${link.href}`)
  })
}

test.describe("♿ RGAA 10.2 — Liens ouvrant une nouvelle fenêtre (site)", () => {
  test.use({ locale: "fr-FR" })

  for (const path of PAGES) {
    test(`Chaque lien target="_blank" annonce la nouvelle fenêtre sur ${path}`, async ({
      page,
    }) => {
      await navigateTo(page, path)
      await expect(page.locator("main a[target='_blank']").first()).toBeAttached()

      expect(await linksOpeningInNewWindowWithoutMention(page)).toEqual([])
    })
  }
})
