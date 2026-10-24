import {
  emptySelection,
  isSelected,
  pageFullySelected,
  selectedCount,
  selectFilter,
  toApiSelection,
  toggle,
  togglePage,
} from "./selection"

describe("selection like in the Django admin", () => {
  it("checks elements of the page", () => {
    let selection = togglePage(emptySelection(), ["1", "2", "3"], true)
    expect(pageFullySelected(selection, ["1", "2", "3"])).toBe(true)
    selection = toggle(selection, "2")
    expect(isSelected(selection, "2")).toBe(false)
    expect(selectedCount(selection, 315)).toBe(2)
    expect(toApiSelection(selection, { afficher: "avalider" }, "groupes")).toEqual({
      mode: "ids",
      ids: [1, 3],
    })
  })

  it("selects everything matching the filter, minus exclusions", () => {
    let selection = selectFilter()
    expect(isSelected(selection, "999")).toBe(true)
    selection = toggle(selection, "4")
    selection = togglePage(selection, ["5", "6"], false)
    expect(selectedCount(selection, 315)).toBe(312)
    expect(
      toApiSelection(
        selection,
        { filtre: "{}", tuples: ["nom"], afficher: "tout" },
        "lignes",
      ),
    ).toEqual({
      mode: "filtre",
      filtre: "{}",
      tuples: ["nom"],
      afficher: "tout",
      exclus: ["4", "5", "6"],
    })
  })
})
