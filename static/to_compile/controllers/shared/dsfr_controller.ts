import { Controller } from "@hotwired/stimulus"

export default class extends Controller<HTMLElement> {
  connect() {
    console.log("[DSFR Controller] Connected to element:", this.element)
    console.log("[DSFR Controller] Element classes:", this.element.className)
    this.makeClickableRows()

    // Listen for turbo:frame-load events to handle dynamically loaded content
    document.addEventListener("turbo:frame-load", this.handleTurboFrameLoad.bind(this))
    console.log("[DSFR Controller] Added turbo:frame-load listener")
  }

  disconnect() {
    console.log("[DSFR Controller] Disconnected")
    document.removeEventListener(
      "turbo:frame-load",
      this.handleTurboFrameLoad.bind(this),
    )
  }

  handleTurboFrameLoad(event: Event) {
    console.log("[DSFR Controller] Turbo frame loaded:", event)
    // Re-run the clickable rows setup when a turbo frame loads
    this.makeClickableRows()
  }

  makeClickableRows() {
    console.log("[DSFR Controller] Looking for tables with .fr-table--clickable-row")

    // Find all tables with the clickable row class within the controller's element
    const clickableTables = this.element.querySelectorAll(".fr-table--clickable-row")
    console.log("[DSFR Controller] Found", clickableTables.length, "clickable tables")

    // Also check if the element itself is a clickable table
    if (this.element.classList.contains("fr-table--clickable-row")) {
      console.log("[DSFR Controller] Element itself is a clickable table")
      this.processTable(this.element, 0)
    }

    clickableTables.forEach((table, tableIndex) => {
      this.processTable(table, tableIndex + 1)
    })
  }

  private processTable(table: Element, tableIndex: number) {
    console.log(`[DSFR Controller] Processing table ${tableIndex}:`, table)

    // Get all rows in the table body
    const rows = table.querySelectorAll("tbody tr")
    console.log(`[DSFR Controller] Table ${tableIndex} has ${rows.length} rows`)

    rows.forEach((row, rowIndex) => {
      // Check if this row already has a click listener to avoid duplicates
      const alreadyClickable = (row as HTMLElement).dataset.dsfrClickable
      if (alreadyClickable) {
        console.log(
          `[DSFR Controller] Row ${rowIndex + 1} already has click listener, skipping`,
        )
        return
      }

      // Look for a link in the row
      const link = row.querySelector("a")

      if (link) {
        console.log(`[DSFR Controller] Row ${rowIndex + 1} has link:`, link.href)

        // Add cursor pointer style to indicate clickability
        ;(row as HTMLElement).style.cursor = "pointer"

        // Mark this row as having a click listener
        ;(row as HTMLElement).dataset.dsfrClickable = "true"

        // Add click event to the row
        row.addEventListener("click", (event) => {
          console.log("[DSFR Controller] Row clicked!")
          console.log("[DSFR Controller] Event target:", event.target)
          console.log("[DSFR Controller] Current target:", event.currentTarget)

          // Prevent navigation if the click was directly on the link itself
          // (to avoid double navigation)
          const target = event.target as HTMLElement
          if (target.tagName === "A" || target.closest("a")) {
            console.log(
              "[DSFR Controller] Click was on or inside a link, letting default behavior happen",
            )
            return
          }

          // Prevent default and stop propagation
          event.preventDefault()
          event.stopPropagation()

          console.log("[DSFR Controller] Navigating to:", link.href)
          // Navigate to the link's href
          window.location.href = link.href
        })

        console.log("[DSFR Controller] Event listener added to row", rowIndex + 1)
      } else {
        console.log(`[DSFR Controller] Row ${rowIndex + 1} has no link`)
      }
    })
  }
}
