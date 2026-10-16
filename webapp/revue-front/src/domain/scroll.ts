/** Scrolls the scrollable container of a table row just enough to show the row
 * entirely, below the sticky header of the table (`scrollIntoView` ignores it,
 * leaving the row hidden under the header when going up). */
export function scrollRowIntoView(row: Element | null) {
  const container = row?.closest(".scroll")
  if (!row || !container) {
    return
  }
  const header = row.closest("table")?.querySelector("thead")
  const headerHeight = header?.getBoundingClientRect().height ?? 0
  const rowBox = row.getBoundingClientRect()
  const box = container.getBoundingClientRect()
  const top = box.top + headerHeight
  if (rowBox.top < top) {
    container.scrollTop -= top - rowBox.top
  } else if (rowBox.bottom > box.bottom) {
    // A row taller than the visible area is aligned on its top
    container.scrollTop += Math.min(rowBox.bottom - box.bottom, rowBox.top - top)
  }
}
