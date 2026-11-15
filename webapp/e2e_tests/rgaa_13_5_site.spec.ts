import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

const PAGES = [
  "/",
  "/bonus-reparation/",
  "/qui-sommes-nous/budget/",
  "/categories/biodechets/dechets-alimentaires/",
  "/categories/vetements/",
]

test.describe("♿ RGAA 13.5 — Émojis cachés aux technologies d'assistance (site)", () => {
  for (const path of PAGES) {
    test(`Aucun émoji visible n'est exposé aux lecteurs d'écran sur ${path}`, async ({
      page,
    }) => {
      await navigateTo(page, path)
      await expect(page.locator("main")).toBeAttached()

      const exposedEmojis = await page.evaluate(() => {
        const emoji = /(?![©®™])\p{Extended_Pictographic}|\p{Regional_Indicator}/u
        const ignoredTags = new Set(["SCRIPT", "STYLE", "TEXTAREA", "OPTION", "svg"])
        const exposed: string[] = []
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
          const text = node.textContent ?? ""
          const parent = node.parentElement
          if (!parent || !emoji.test(text) || ignoredTags.has(parent.tagName)) continue
          if (!parent.checkVisibility()) continue
          if (parent.closest('[aria-hidden="true"]')) continue
          exposed.push(text.trim().slice(0, 60))
        }
        return exposed
      })

      expect(exposedEmojis).toEqual([])
    })
  }
})
