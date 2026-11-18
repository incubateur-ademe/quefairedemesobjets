import { fireEvent, screen, waitFor } from "@testing-library/react"

import type { Cohorte } from "../../api/types"
import { fakeApi, renderApp } from "../../test-utils"
import { CohortesScreen } from "./CohortesScreen"

const cohorte = (id: number, patch: Partial<Cohorte> = {}): Cohorte => ({
  id,
  identifiant_action: `dag_${id}`,
  identifiant_execution: "manual__2026-10-01T06:00:00",
  execution_datetime: "01/10/2026 06:00",
  type_action: "SOURCE_MODIFICATION",
  type_action_label: "modification",
  statut: "AVALIDER",
  cree_le: "2026-10-01T06:00:00Z",
  metadata: { source_code: "ecomaison" },
  total_groupes: 4,
  compteurs: { AVALIDER: 3, ATRAITER: 1, REJETEE: 0, ENCOURS: 0, SUCCES: 0, ERREUR: 0 },
  logs: { ERROR: 1, WARNING: 0, INFO: 0 },
  ...patch,
})

function setup(url = "/data/revue/") {
  const api = fakeApi((path) =>
    path.endsWith("/filtres")
      ? { champs: [] }
      : path.endsWith("/logs")
        ? { items: [], total: 0, page: 1, page_size: 100 }
        : { items: [cohorte(1), cohorte(2)], total: 2, page: 1, page_size: 50 },
  )
  renderApp(<CohortesScreen />, { api, url })
  return api
}

const lastCohortesQuery = (api: ReturnType<typeof setup>) =>
  api.GET.mock.calls.filter(([path]) => path === "/api/suggestions/cohortes").at(-1)![1]
    .params.query

describe("CohortesScreen", () => {
  it("lists the cohortes with their progress", async () => {
    setup()

    expect(await screen.findByText("dag_1")).toBeInTheDocument()
    expect(screen.getByText("dag_2").closest("a")).toHaveAttribute(
      "href",
      "/data/revue/cohortes/2",
    )
    expect(screen.getAllByText("25 %")).toHaveLength(2)
    expect(screen.getByText("2 cohortes SOURCE")).toBeInTheDocument()
  })

  it("sends quick filters and sort to the API, and keeps them in the URL", async () => {
    const api = setup()
    await screen.findByText("dag_1")

    fireEvent.click(screen.getByText("Suppression"))
    fireEvent.click(screen.getByText("Type", { selector: "th" }))

    await waitFor(() =>
      expect(lastCohortesQuery(api)).toMatchObject({
        type_action: ["SOURCE_SUPRESSION"],
        tri: "type_action",
        page: 1,
      }),
    )
    expect(window.location.search).toBe("?type=SOURCE_SUPRESSION&tri=type_action")
  })

  it("restores its state from the URL", async () => {
    const filtre = JSON.stringify({
      op: "and",
      conditions: [{ field: "id", operator: "eq", value: 1 }],
    })
    const api = setup(
      `/data/revue/?page=2&par_page=25&filtre=${encodeURIComponent(filtre)}`,
    )
    await screen.findByText("dag_1")

    expect(lastCohortesQuery(api)).toMatchObject({ page: 2, page_size: 25, filtre })
  })

  it("opens the logs drawer", async () => {
    setup()
    await screen.findByText("dag_1")

    fireEvent.click(screen.getAllByText("Logs", { selector: "wa-button" })[0])

    expect(window.location.search).toBe("?logs=1")
    expect(document.querySelector("wa-drawer")).toHaveAttribute(
      "label",
      "Logs de la cohorte #1",
    )
  })
})
