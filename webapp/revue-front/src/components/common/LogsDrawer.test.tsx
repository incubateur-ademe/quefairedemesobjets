import { fireEvent, screen } from "@testing-library/react"

import { fakeApi, renderApp } from "../../test-utils"
import { LogsDrawer, logsExportUrl } from "./LogsDrawer"

describe("logsExportUrl", () => {
  it("keeps the level filter", () => {
    expect(logsExportUrl("/api/suggestions", 4, [])).toBe(
      "/api/suggestions/cohortes/4/logs/export",
    )
    expect(logsExportUrl("/api/suggestions", 4, ["ERROR", "INFO"])).toBe(
      "/api/suggestions/cohortes/4/logs/export?niveau=ERROR&niveau=INFO",
    )
  })
})

describe("LogsDrawer", () => {
  it("offers the Excel export of the filtered logs", async () => {
    const api = fakeApi(() => ({ items: [], total: 0, page: 1, page_size: 100 }))
    renderApp(<LogsDrawer cohorteId={7} onClose={jest.fn()} />, {
      api,
      url: "/data/revue/?logs=7",
    })
    const exportButton = () =>
      screen.getByText("Exporter en Excel").closest("wa-button")!

    expect(exportButton()).toHaveAttribute(
      "href",
      "/api/suggestions/cohortes/7/logs/export",
    )

    fireEvent.click(screen.getByText("erreurs"))

    expect(exportButton()).toHaveAttribute(
      "href",
      "/api/suggestions/cohortes/7/logs/export?niveau=ERROR",
    )
    expect(await screen.findByText("Aucun log.")).toBeInTheDocument()
  })
})
