import { render, screen } from "@testing-library/react"

import { LogsButton } from "./LogsButton"

describe("LogsButton", () => {
  it("takes the color and icon of the most severe level", () => {
    render(
      <LogsButton
        cohorteId={1}
        logs={{ ERROR: 0, WARNING: 2, INFO: 1 }}
        onOpen={jest.fn()}
      />,
    )
    const button = screen.getByText("Logs").closest("wa-button")!

    expect(button.getAttribute("variant")).toBe("warning")
    expect(button.querySelector("wa-icon")!.getAttribute("name")).toBe("alert")
    expect(screen.getByText("2 avertissements · 1 info")).toBeInTheDocument()
  })

  it("is neutral without logs", () => {
    render(
      <LogsButton
        cohorteId={1}
        logs={{ ERROR: 0, WARNING: 0, INFO: 0 }}
        onOpen={jest.fn()}
      />,
    )

    expect(screen.getByText("Logs").closest("wa-button")!.getAttribute("variant")).toBe(
      "neutral",
    )
    expect(screen.getByText("aucun log")).toBeInTheDocument()
  })
})
