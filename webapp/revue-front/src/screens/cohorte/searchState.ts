/** Navigation state of screen 2, read from and written to the URL. */
import type { Afficher, Vue } from "../../api/types"

export const PAGE_SIZES: Record<Vue, number[]> = {
  groupes: [25, 50, 100, 200],
  lignes: [100, 250, 500, 1000],
}
export const DEFAULT_PAGE_SIZE: Record<Vue, number> = { groupes: 100, lignes: 500 }

export type ReviewState = {
  vue: Vue
  afficher: Afficher
  filtre?: string
  tuples: string[]
  page: number
  pageSize: number
  /** View « Groupes »: hides the lignes already validated */
  masquerValidees: boolean
}

/** Tuples are written « champ,champ » and separated by « | » in the URL. */
export const TUPLES_SEPARATOR = "|"

export function readReviewState(search: Record<string, string>): ReviewState {
  const vue: Vue = search.vue === "lignes" ? "lignes" : "groupes"
  const pageSize = Number(search.par_page)
  return {
    vue,
    afficher: search.afficher === "tout" ? "tout" : "avalider",
    filtre: search.filtre || undefined,
    tuples: search.tuples ? search.tuples.split(TUPLES_SEPARATOR).filter(Boolean) : [],
    page: Number(search.page) || 1,
    pageSize: PAGE_SIZES[vue].includes(pageSize) ? pageSize : DEFAULT_PAGE_SIZE[vue],
    masquerValidees: search.masquer_validees === "1",
  }
}
