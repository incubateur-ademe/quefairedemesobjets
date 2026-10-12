import { fireEvent, screen, waitFor, within } from "@testing-library/react"

import { fakeApi, renderApp } from "../../test-utils"
import { CohorteScreen } from "./CohorteScreen"
import { COHORTE, groupe, page, STATS } from "./fixtures"

const COUNTS = {
  validate: 2,
  reject: 2,
  resubmit: 0,
  report_correction: 1,
  report_parent: 0,
}

function setup(total = 2) {
  const api = fakeApi((path, options, method) => {
    if (path.endsWith("/actions/apercu")) return { compteurs: COUNTS }
    if (path.endsWith("/actions")) return { affected: 2, skipped: 0 }
    if (method !== "GET") return groupe(1)
    if (path.endsWith("/stats")) return STATS
    if (path.endsWith("/revue/filtres")) return { champs: [] }
    if (path.endsWith("/groupes")) {
      const query = (options as { params: { query: { afficher: string } } }).params
        .query
      // Reload after the action (filter on the ids, « tout »)
      if (query.afficher === "tout") {
        return page([
          groupe(1, { statut: "ATRAITER" }),
          groupe(2, { statut: "ATRAITER" }),
        ])
      }
      return { ...page([groupe(1), groupe(2)]), total }
    }
    return COHORTE
  })
  renderApp(<CohorteScreen cohorteId={7} />, { api, url: "/data/revue/cohortes/7" })
  return api
}

const bar = () => screen.getByRole("region", { name: "Sélection" })
const header = (id: number) =>
  document.querySelector(`[data-cursor="g:${id}"]`) as HTMLElement

describe("MassBar", () => {
  it("selects the page, then everything matching the filter, and validates", async () => {
    const api = setup(315)
    await screen.findByText("Acteur 1")

    fireEvent.click(screen.getByLabelText("Sélectionner les groupes de cette page"))
    expect(within(bar()).getByText("2 groupes")).toBeInTheDocument()
    fireEvent.click(
      screen.getByText("Sélectionner les 315 groupes répondant au filtre"),
    )
    expect(within(bar()).getByText("315 groupes")).toBeInTheDocument()

    // Excluding a groupe of the page
    fireEvent.click(within(header(2)).getByLabelText("Sélectionner le groupe 2"))
    expect(within(bar()).getByText("314 groupes")).toBeInTheDocument()
    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith(
        "/api/suggestions/cohortes/{cohorte_id}/actions/apercu",
        {
          params: { path: { cohorte_id: 7 } },
          body: {
            vue: "groupes",
            selection: {
              mode: "filtre",
              afficher: "avalider",
              tuples: [],
              exclus: [2],
            },
          },
        },
      ),
    )

    // « Tout le filtre »: confirmation required
    fireEvent.click(await within(bar()).findByText(/Valider/))
    const dialog = document.querySelector("wa-dialog.confirm-dialog") as HTMLElement
    expect(dialog).toHaveAttribute("open")
    expect(within(dialog).getByText(/toutes les pages du filtre/)).toBeInTheDocument()
    fireEvent.click(within(dialog).getByText("Confirmer"))

    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith(
        "/api/suggestions/cohortes/{cohorte_id}/actions",
        {
          params: { path: { cohorte_id: 7 } },
          body: {
            vue: "groupes",
            action: "validate",
            selection: {
              mode: "filtre",
              afficher: "avalider",
              tuples: [],
              exclus: [2],
            },
          },
        },
      ),
    )
    // The groupes of the page are reloaded and stay on screen with their statut
    await waitFor(() =>
      expect(within(header(1)).getByText("Validé")).toBeInTheDocument(),
    )
    expect(screen.queryByRole("region", { name: "Sélection" })).toBeNull()
  })

  it("runs a small action without confirmation, and X checks the cursor", async () => {
    const api = setup()
    await screen.findByText("Acteur 1")

    fireEvent.click(header(1))
    fireEvent.keyDown(window, { key: "x" })
    expect(within(header(1)).getByLabelText("Sélectionner le groupe 1")).toBeChecked()
    // The page is entirely selected but all the filter is on the page: no link
    expect(screen.queryByText(/répondant au filtre/)).toBeNull()

    fireEvent.click(await within(bar()).findByText(/Reporter vers la correction/))

    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith(
        "/api/suggestions/cohortes/{cohorte_id}/actions",
        {
          params: { path: { cohorte_id: 7 } },
          body: {
            vue: "groupes",
            action: "report_correction",
            selection: { mode: "ids", ids: [1] },
          },
        },
      ),
    )
  })

  it("always confirms a refusal, and disables actions concerning nothing", async () => {
    setup()
    await screen.findByText("Acteur 1")
    fireEvent.click(within(header(1)).getByLabelText("Sélectionner le groupe 1"))

    const resubmit = await within(bar()).findByText(/Remettre à valider/)
    await waitFor(() =>
      expect(resubmit.closest("wa-button")).toHaveAttribute("disabled"),
    )
    fireEvent.click(within(bar()).getByText(/Refuser/))

    expect(document.querySelector("wa-dialog.confirm-dialog")).toHaveAttribute("open")
  })
})
