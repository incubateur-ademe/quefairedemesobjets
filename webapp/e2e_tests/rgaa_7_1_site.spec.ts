import { expect, test } from "@playwright/test"
import { navigateTo } from "./helpers"

test.describe("♿ RGAA 7.1 — Notes de bas de page accessibles", () => {
  test("La page Déchets alimentaires expose des notes de bas de page accessibles", async ({
    page,
  }) => {
    await navigateTo(page, "/categories/biodechets/dechets-alimentaires/")

    const calls = page.getByRole("link", { name: "Note de bas de page 1" })
    await expect(calls).toHaveCount(2)
    for (const call of await calls.all()) {
      await expect(call).toHaveAttribute("href", "#note-1")
      await expect(call).toHaveAttribute("aria-describedby", "note-1")
      await expect(call).toHaveText("1")
      expect(await call.evaluate((el) => el.parentElement?.tagName)).toBe("SUP")
    }
    await expect(calls.first()).toHaveAttribute("id", "appel-note-1")

    const note = page.locator("ol > li#note-1")
    await expect(note).toHaveAttribute("tabindex", "-1")
    await expect(note).toContainText("Librairie ADEME")

    const backLink = note.getByRole("link", { name: "[1] retour au texte" })
    await expect(backLink).toHaveText("[1]")
    await expect(backLink).toHaveAttribute("href", "#appel-note-1")

    await calls.first().click()
    await expect(page).toHaveURL(/#note-1$/)
    await backLink.click()
    await expect(page).toHaveURL(/#appel-note-1$/)
  })
})
