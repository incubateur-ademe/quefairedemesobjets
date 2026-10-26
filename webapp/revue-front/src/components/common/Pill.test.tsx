import { render, screen } from "@testing-library/react"

import { StatutPill } from "./Pill"

describe("StatutPill", () => {
  it("shows the decision in title", () => {
    render(
      <StatutPill
        statut="REJETEE"
        decision={{ par: { username: "nicolas" }, le: "2026-10-22T19:42:00Z" }}
      />,
    )

    expect(screen.getByText("Rejeté").closest(".pill")!.getAttribute("title")).toMatch(
      /^nicolas · 22\/10\/2026/,
    )
  })

  it("has no title without decision", () => {
    render(<StatutPill statut="AVALIDER" decision={{ par: null, le: null }} />)

    expect(screen.getByText("À valider").closest(".pill")!.hasAttribute("title")).toBe(
      false,
    )
  })
})
