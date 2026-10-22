import { act, fireEvent, screen, waitFor, within } from "@testing-library/react"

import { FakeApiError, fakeApi, renderApp, setControlValue } from "../../test-utils"
import { CohorteScreen } from "./CohorteScreen"
import { COHORTE, groupe, ligne, page, STATS } from "./fixtures"

type Answer = (path: string, options: unknown, method: string) => unknown

function setup(write: Answer = () => groupe(1), url = "/data/revue/cohortes/7") {
  const api = fakeApi((path, options, method) => {
    if (method !== "GET") {
      return write(path, options, method)
    }
    if (path.endsWith("/stats")) return STATS
    if (path.endsWith("/revue/filtres")) return { champs: [] }
    if (path.endsWith("/groupes")) return page([groupe(1), groupe(2)])
    return COHORTE
  })
  renderApp(<CohorteScreen cohorteId={7} />, { api, url })
  return api
}

const headerOf = (id: number) =>
  document.querySelector(`[data-cursor="g:${id}"]`) as HTMLElement

describe("CohorteScreen", () => {
  it("shows the header, counters, tuples and groupes", async () => {
    setup()

    expect(await screen.findByText("dag_ecomaison")).toBeInTheDocument()
    expect(await screen.findByText("Acteur 1")).toBeInTheDocument()
    expect(screen.getByText("Groupes du filtre")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /^nom/ })).toBeInTheDocument()
    expect(within(headerOf(1)).getByText("0/2 lignes")).toBeInTheDocument()
  })

  it("validates the groupe under the cursor with A and moves to the next groupe", async () => {
    let resolve: (value: unknown) => void = () => {}
    const api = setup(() => new Promise((r) => (resolve = r)))
    await screen.findByText("Acteur 1")

    fireEvent.click(headerOf(1))
    fireEvent.keyDown(window, { key: "a" })

    // Optimistic: validated before the server answers
    await waitFor(() =>
      expect(within(headerOf(1)).getByText("Validé")).toBeInTheDocument(),
    )
    expect(headerOf(2)).toHaveClass("cur")
    expect(api.POST).toHaveBeenCalledWith(
      "/api/suggestions/groupes/{groupe_id}/decision",
      {
        params: { path: { groupe_id: 1 } },
        body: { action: "validate", expected_modifie_le: "2026-10-09T10:00:00.000Z" },
      },
    )

    await act(async () => resolve(groupe(1, { statut: "ATRAITER" })))
    // The validated groupe stays on screen
    expect(within(headerOf(1)).getByText("Validé")).toBeInTheDocument()
  })

  it("hides the lignes already validated, if asked", async () => {
    const api = fakeApi((path) => {
      if (path.endsWith("/stats")) return STATS
      if (path.endsWith("/revue/filtres")) return { champs: [] }
      if (path.endsWith("/groupes"))
        return page([
          groupe(1, {
            lignes: [ligne(1, ["nom"], { statut: "ATRAITER" }), ligne(1, ["url"])],
          }),
        ])
      return COHORTE
    })
    renderApp(<CohorteScreen cohorteId={7} />, { api, url: "/data/revue/cohortes/7" })
    await screen.findByText("Acteur 1")
    const ligneRow = (key: string) => document.querySelector(`[data-cursor="l:${key}"]`)
    expect(ligneRow("1:nom")).toBeInTheDocument()

    fireEvent.click(screen.getByLabelText("Masquer les lignes déjà validées"))

    await waitFor(() => expect(ligneRow("1:nom")).not.toBeInTheDocument())
    expect(ligneRow("1:url")).toBeInTheDocument()
    expect(window.location.search).toBe("?masquer_validees=1")
    // The keyboard skips the hidden lignes
    fireEvent.click(headerOf(1))
    fireEvent.keyDown(window, { key: "ArrowDown" })
    expect(ligneRow("1:url")).toHaveClass("cur")
  })

  it("reloads the groupe and notifies on a conflict", async () => {
    setup(
      () =>
        new FakeApiError(409, {
          code: "conflict",
          detail: "Ce groupe a été modifié entre-temps",
          current: groupe(1, {
            statut: "REJETEE",
            capacites: { ...groupe(1).capacites, valider: false },
          }),
        }),
    )
    await screen.findByText("Acteur 1")

    fireEvent.click(within(headerOf(1)).getByText("Valider le groupe"))

    expect(
      await screen.findByText(/Ce groupe a été modifié entre-temps/),
    ).toBeInTheDocument()
    expect(within(headerOf(1)).getByText("Rejeté")).toBeInTheDocument()
  })

  it("shows the validation error of a correction on its field", async () => {
    const api = setup(
      () =>
        new FakeApiError(422, {
          code: "validation",
          detail: "Valeur refusée",
          errors: { url: ["Saisissez une URL valide."] },
        }),
    )
    await screen.findByText("Acteur 1")
    const row = document.querySelector('[data-cursor="l:1:url"]') as HTMLElement

    fireEvent.click(within(row).getByTitle("Proposer une valeur"))
    setControlValue(row.querySelector('wa-input[label="url"]')!, "pas une url", "input")
    fireEvent.submit(row.querySelector("form")!)

    expect(
      await within(row).findByText("Saisissez une URL valide."),
    ).toBeInTheDocument()
    expect(api.PUT).toHaveBeenCalledWith(
      "/api/suggestions/groupes/{groupe_id}/propositions",
      {
        params: { path: { groupe_id: 1 } },
        body: {
          suggestion_modele: "RevisionActeur",
          champs: ["url"],
          valeurs: { url: "pas une url" },
          expected_modifie_le: "2026-10-09T10:00:00.000Z",
        },
      },
    )
    expect(screen.queryByText(/Valeur refusée/)).not.toBeInTheDocument()
  })

  it("keeps the view state in the URL", async () => {
    const api = setup()
    await screen.findByText("Acteur 1")

    fireEvent.click(screen.getByText("Tout"))
    fireEvent.click(screen.getByRole("button", { name: /^nom/ }))

    await waitFor(() =>
      expect(window.location.search).toBe("?afficher=tout&tuples=nom"),
    )
    const groupesCalls = api.GET.mock.calls.filter(([path]) =>
      path.endsWith("/groupes"),
    )
    expect(groupesCalls.at(-1)![1].params.query).toMatchObject({
      afficher: "tout",
      tuples: ["nom"],
      page: 1,
      page_size: 100,
    })
  })
})

describe("CohorteScreen shortcuts", () => {
  it("puts back to validate the groupe under the cursor with U", async () => {
    const validated = groupe(1, {
      statut: "ATRAITER",
      capacites: {
        ...groupe(1).capacites,
        valider: false,
        refuser: false,
        remettre_a_valider: true,
      },
    })
    const api = fakeApi((path, _options, method) => {
      if (method !== "GET") return groupe(1)
      if (path.endsWith("/stats")) return STATS
      if (path.endsWith("/revue/filtres")) return { champs: [] }
      if (path.endsWith("/groupes")) return page([validated, groupe(2)])
      return COHORTE
    })
    renderApp(<CohorteScreen cohorteId={7} />, {
      api,
      url: "/data/revue/cohortes/7?afficher=tout",
    })
    await screen.findByText("Acteur 1")

    fireEvent.click(headerOf(1))
    fireEvent.keyDown(window, { key: "u" })

    await waitFor(() =>
      expect(within(headerOf(1)).getByText("À valider")).toBeInTheDocument(),
    )
    expect(headerOf(1)).toHaveClass("cur")
    expect(api.POST).toHaveBeenCalledWith(
      "/api/suggestions/groupes/{groupe_id}/decision",
      {
        params: { path: { groupe_id: 1 } },
        body: { action: "resubmit", expected_modifie_le: "2026-10-09T10:00:00.000Z" },
      },
    )
  })

  it("lists the shortcuts in the tooltip of « ? raccourcis »", async () => {
    setup()
    await screen.findByText("Acteur 1")

    expect(screen.getByText("? raccourcis")).toHaveAttribute("id", "shortcuts-revue")
    expect(
      document.querySelector('wa-tooltip[for="shortcuts-revue"]'),
    ).toHaveTextContent(/remettre à valider/)
  })
})
