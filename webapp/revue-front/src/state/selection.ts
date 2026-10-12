/** Selection, like in the Django admin:
 * - « page » mode: the elements checked (groupe ids or ligne keys);
 * - « filtre » mode: every element matching the filter (all pages), except the
 *   unchecked ones. The server applies the filter again for the action. */
export type Selection =
  | { mode: "page"; ids: ReadonlySet<string> }
  | { mode: "filtre"; exclus: ReadonlySet<string> }

export const emptySelection = (): Selection => ({ mode: "page", ids: new Set() })

export function isSelected(selection: Selection, id: string) {
  return selection.mode === "page" ? selection.ids.has(id) : !selection.exclus.has(id)
}

/** Number of selected elements; `total` is the number matching the filter. */
export function selectedCount(selection: Selection, total: number) {
  return selection.mode === "page"
    ? selection.ids.size
    : Math.max(0, total - selection.exclus.size)
}

export function toggle(selection: Selection, id: string): Selection {
  const set = new Set(selection.mode === "page" ? selection.ids : selection.exclus)
  if (!set.delete(id)) {
    set.add(id)
  }
  return selection.mode === "page"
    ? { mode: "page", ids: set }
    : { mode: "filtre", exclus: set }
}

/** Header checkbox: checks or unchecks every element of the page. */
export function togglePage(
  selection: Selection,
  pageIds: string[],
  checked: boolean,
): Selection {
  if (selection.mode === "filtre") {
    const exclus = new Set(selection.exclus)
    pageIds.forEach((id) => (checked ? exclus.delete(id) : exclus.add(id)))
    return { mode: "filtre", exclus }
  }
  const ids = new Set(selection.ids)
  pageIds.forEach((id) => (checked ? ids.add(id) : ids.delete(id)))
  return { mode: "page", ids }
}

export const selectFilter = (): Selection => ({ mode: "filtre", exclus: new Set() })

export function pageFullySelected(selection: Selection, pageIds: string[]) {
  return pageIds.length > 0 && pageIds.every((id) => isSelected(selection, id))
}

export type ListFilter = {
  filtre?: string
  tuples?: string[]
  afficher: "avalider" | "tout"
}

/** Selection sent to the API. */
export function toApiSelection(
  selection: Selection,
  list: ListFilter,
  vue: "groupes" | "lignes",
) {
  const id = (value: string) => (vue === "groupes" ? Number(value) : value)
  return selection.mode === "page"
    ? { mode: "ids" as const, ids: [...selection.ids].map(id) }
    : {
        mode: "filtre" as const,
        filtre: list.filtre,
        tuples: list.tuples ?? [],
        afficher: list.afficher,
        exclus: [...selection.exclus].map(id),
      }
}
