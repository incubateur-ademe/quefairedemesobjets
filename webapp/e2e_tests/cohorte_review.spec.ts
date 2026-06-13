import { execSync } from "node:child_process"
import { expect, Page } from "@playwright/test"
import { test } from "./fixtures"
import { navigateTo, TIMEOUT } from "./helpers"

/**
 * E2E coverage for the cohorte review screen (data:cohorte_review).
 *
 * The screen is a virtualized TanStack grid driven by a single Stimulus
 * controller. These tests guard the behaviours that browser testing caught
 * regressing silently: row selection, optimistic per-cell decisions, the
 * keyboard review loop, and bulk undo.
 *
 * Data is seeded by the `seed_review_e2e` management command, which builds a
 * deterministic, self-contained cohorte (its own acteurs) so the suite works
 * against an empty sample database.
 */

let cohorteId: string

// Reseed before each test: the suite runs serially against a shared sample
// DB and the tests mutate suggestion statuts, so a deterministic starting
// state per test is required for the exact-count assertions.
function seedReviewCohorte() {
  const databaseUrl = process.env.SAMPLE_DATABASE_URL ?? process.env.DATABASE_URL ?? ""
  const output = execSync("uv run python manage.py seed_review_e2e", {
    encoding: "utf-8",
    env: { ...process.env, DATABASE_URL: databaseUrl },
  })
  const match = output.match(/COHORTE_ID=(\d+)/)
  if (!match) {
    throw new Error(`seed_review_e2e did not report a cohorte id:\n${output}`)
  }
  cohorteId = match[1]
}

async function loginAsAdmin(page: Page) {
  await navigateTo(page, "/admin/login/")
  await page.locator('input[name="username"]').fill("admin")
  await page.locator('input[name="password"]').fill("admin")
  await page.locator('[type="submit"]').click()
  await page.waitForURL("**/admin/")
}

async function openReview(page: Page, query = "") {
  await navigateTo(page, `/data/cohorte/${cohorteId}/review/${query}`)
  // wait until the grid (or focus cards) has rendered its first rows
  await expect(page.locator(".status")).not.toHaveText("Chargement…", {
    timeout: TIMEOUT.DEFAULT,
  })
}

test.describe("🗂️ Revue de cohorte — grille", () => {
  test.beforeEach(async ({ page }) => {
    seedReviewCohorte()
    await loginAsAdmin(page)
  })

  test("la grille pivot charge les acteurs et leurs champs", async ({ page }) => {
    await openReview(page)

    await expect(page.locator("tbody tr[data-groupe-id]").first()).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })
    // nom + telephone columns are present as focus-entry badges
    await expect(page.locator('thead .focus-entry[data-field="nom"]')).toBeVisible()
    await expect(
      page.locator('thead .focus-entry[data-field="telephone"]'),
    ).toBeVisible()
  })

  test("accepter une cellule la marque acceptée (UI optimiste)", async ({ page }) => {
    await openReview(page)

    const firstPendingCell = page.locator("td.sug.pending").first()
    await expect(firstPendingCell).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    await firstPendingCell.locator(".cell-action.accept").click()

    // the cell flips to accepted, no full reload
    await expect(page.locator("td.sug.accepted").first()).toBeVisible({
      timeout: TIMEOUT.SHORT,
    })
    // and no JS error broke the controller (status keeps updating)
    await expect(page.locator(".status")).toContainText("acteurs")
  })

  test("sélection multi-lignes puis rejet de masse, avec annulation", async ({
    page,
  }) => {
    await openReview(page)

    const rows = page.locator("tbody tr[data-groupe-id]")
    await expect(rows.first()).toBeVisible({ timeout: TIMEOUT.DEFAULT })

    // select the first two rows
    await rows.nth(0).locator("sl-checkbox").click()
    await rows.nth(1).locator("sl-checkbox").click()

    // the bulk bar reports exactly 2 (guards the pagination-state bug)
    const bulkBar = page.locator('[data-cohorte-review-target="bulkBar"]')
    await expect(bulkBar).toBeVisible()
    await expect(page.locator('[data-cohorte-review-target="bulkCount"]')).toHaveText(
      "2",
    )

    // reject the selection
    await page
      .locator('sl-button[data-action="click->cohorte-review#bulkReject"]')
      .click()

    // an undo toast appears
    const toast = page.locator(".undo-toast")
    await expect(toast).toBeVisible({ timeout: TIMEOUT.SHORT })
    await expect(toast).toContainText("rejetée")

    // undo restores the rows to « à valider »
    await page.locator(".undo-toast-action").click()
    await expect(toast).toBeHidden({ timeout: TIMEOUT.SHORT })
    await expect(page.locator('[data-cohorte-review-target="announcer"]')).toHaveText(
      "Action annulée",
    )
    await expect(page.locator("td.sug.rejected")).toHaveCount(0)
  })
})

test.describe("🎯 Revue de cohorte — mode focus", () => {
  test.beforeEach(async ({ page }) => {
    seedReviewCohorte()
    await loginAsAdmin(page)
  })

  test("le badge 🎯 d'une colonne ouvre le mode focus", async ({ page }) => {
    await openReview(page)

    await page.locator('thead .focus-entry[data-field="telephone"]').click()

    await expect(page).toHaveURL(/\?focus=telephone/)
    await expect(page.locator(".focus-layout")).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })
    await expect(page.locator(".focus-card").first()).toBeVisible()
    await expect(page.locator(".focus-card.active")).toHaveCount(1)
  })

  test("la revue au clavier : ↓ navigue, A accepte et avance", async ({ page }) => {
    await openReview(page, "?focus=telephone")

    const cards = page.locator(".focus-card")
    await expect(cards.first()).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    const initialCount = await cards.count()

    // move down then accept the active card
    await page.keyboard.press("ArrowDown")
    await page.keyboard.press("a")

    // a card became accepted
    await expect(page.locator(".focus-card.accepted").first()).toBeVisible({
      timeout: TIMEOUT.SHORT,
    })
    // and the active cursor advanced (still exactly one active card)
    await expect(page.locator(".focus-card.active")).toHaveCount(1)
    // total cards unchanged (decided rows stay visible in place)
    await expect(cards).toHaveCount(initialCount)
  })

  test("le query builder filtre par valeur suggérée", async ({ page }) => {
    await openReview(page, "?focus=telephone")
    await expect(page.locator(".focus-card").first()).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    // « commence par 07 » matches the crafted subset (positions 0,3,6,9 → 4)
    await page.locator(".vb-row .vb-value").first().fill("07")
    await page.locator('sl-button[data-action="click->cohorte-review#vbApply"]').click()

    await expect(page.locator(".vb-active")).toContainText("filtre actif", {
      timeout: TIMEOUT.SHORT,
    })
    await expect(page.locator(".focus-card")).toHaveCount(4)
  })

  test("Échap quitte le mode focus", async ({ page }) => {
    await openReview(page, "?focus=telephone")
    await expect(page.locator(".focus-layout")).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    await page.keyboard.press("Escape")

    await expect(page).not.toHaveURL(/\?focus=/)
    await expect(page.locator(".focus-layout")).toBeHidden()
    await expect(page.locator(".table-wrap")).toBeVisible()
  })
})
