import { render, screen, waitFor, within } from "@testing-library/react"

import type { Tache } from "../../api/types"
import { fakeApi, renderApp } from "../../test-utils"
import { CohorteScreen } from "./CohorteScreen"
import { COHORTE, groupe, page, STATS } from "./fixtures"
import { TachesButton, TachesDrawer } from "./Taches"

function tache(id: string, patch: Partial<Tache> = {}): Tache {
  return {
    id,
    statut: "done",
    action: "report_correction",
    groupes: 1200,
    affected: 1150,
    par: "admin",
    lancee_le: "2026-10-09T10:00:00Z",
    debut: "2026-10-09T10:00:01Z",
    fin: "2026-10-09T10:02:00Z",
    erreur: "",
    ...patch,
  }
}

describe("TachesButton", () => {
  it("shows the number of tasks and those running", () => {
    render(
      <TachesButton
        taches={[tache("a", { statut: "running" }), tache("b")]}
        onOpen={jest.fn()}
      />,
    )
    const button = screen.getByText(/^Tâches/).closest("wa-button")!

    expect(button).toHaveTextContent("Tâches 2· 1 en cours")
    expect(button.getAttribute("variant")).toBe("brand")
    expect(button.querySelector("wa-spinner")).not.toBeNull()
    expect(screen.getByText("1 en cours · 1 terminée")).toBeInTheDocument()
  })

  it("is neutral without task, and red after a failure", () => {
    const { rerender } = render(<TachesButton taches={[]} onOpen={jest.fn()} />)
    const button = () => screen.getByText(/^Tâches/).closest("wa-button")!
    expect(button().getAttribute("variant")).toBe("neutral")
    expect(screen.getByText("aucune tâche")).toBeInTheDocument()

    rerender(
      <TachesButton taches={[tache("a", { statut: "error" })]} onOpen={jest.fn()} />,
    )
    expect(button().getAttribute("variant")).toBe("danger")
    expect(button().querySelector("wa-spinner")).toBeNull()
  })
})

describe("TachesDrawer", () => {
  it("lists the tasks with their result", () => {
    render(
      <TachesDrawer
        cohorteId={7}
        open
        taches={[
          tache("a", { statut: "running", fin: null, affected: null }),
          tache("b", { action: "report_parent" }),
          tache("c", { statut: "error", erreur: "OperationalError" }),
        ]}
        onClose={jest.fn()}
      />,
    )
    const rows = screen.getAllByRole("row").slice(1)

    expect(within(rows[0]).getByText("En cours")).toBeInTheDocument()
    expect(screen.getByText(/Mise à jour automatique/)).toBeInTheDocument()
    expect(within(rows[1]).getByText("Report vers le parent")).toBeInTheDocument()
    expect(within(rows[1]).getByText("1 150 groupes modifiés")).toBeInTheDocument()
    expect(within(rows[2]).getByText("OperationalError")).toBeInTheDocument()
  })
})

describe("useTaches", () => {
  it("polls a running task, then reloads the groupes of the page when it ends", async () => {
    let calls = 0
    const api = fakeApi((path) => {
      if (path.endsWith("/stats")) return STATS
      if (path.endsWith("/taches")) {
        calls += 1
        return [tache("a", { statut: calls === 1 ? "running" : "done" })]
      }
      if (path.endsWith("/revue/filtres")) return { champs: [] }
      if (path.endsWith("/groupes")) return page([groupe(1)])
      return COHORTE
    })
    renderApp(<CohorteScreen cohorteId={7} />, { api, url: "/data/revue/cohortes/7" })

    expect(await screen.findByText("· 1 en cours")).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByText("· 1 en cours")).toBeNull(), {
      timeout: 4000,
    })
    // Reload of the page by ids, « tout »
    await waitFor(() =>
      expect(
        api.GET.mock.calls.some(
          ([path, options]) =>
            path.endsWith("/groupes") && options.params.query.afficher === "tout",
        ),
      ).toBe(true),
    )
  })
})
