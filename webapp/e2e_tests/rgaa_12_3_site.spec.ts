import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

const LINK_BATCH_SIZE = 5
const CRAWL_TIMEOUT_MS = 180_000

test.describe("♿ RGAA 12.3 — Plan du site pertinent", () => {
  test.use({ locale: "fr-FR" })

  test("Le plan du site est une liste courte, sans lien mort ni fiche produit", async ({
    page,
  }) => {
    test.setTimeout(CRAWL_TIMEOUT_MS)
    await navigateTo(page, "/plan-du-site/")

    const main = page.getByRole("main")
    await expect(main.getByRole("heading", { level: 1 })).toHaveText("Plan du site")

    const plan = main.locator("ul").first()
    const links = plan.getByRole("link")

    await expect(links.first()).toHaveAttribute("href", "/")
    await expect(links.first()).toHaveText(
      "Page d'accueil - Rechercher un objet ou un déchet",
    )

    const hrefs = await links.evaluateAll((anchors) =>
      anchors.map((a) => a.getAttribute("href") ?? ""),
    )
    expect(new Set(hrefs).size).toBe(hrefs.length)
    for (const href of hrefs) {
      expect(href, href).toMatch(/^\/[^\s]*$/)
      expect(href, href).not.toMatch(/^\/(dechet|tests?)(\/|$)/)
    }

    const failures: string[] = []
    for (let i = 0; i < hrefs.length; i += LINK_BATCH_SIZE) {
      const batch = hrefs.slice(i, i + LINK_BATCH_SIZE)
      const statuses = await Promise.all(
        batch.map((href) => page.request.get(href).then((r) => r.status())),
      )
      statuses.forEach((status, index) => {
        if (status >= 400) failures.push(`${batch[index]} -> ${status}`)
      })
    }
    expect(failures).toEqual([])
  })
})
