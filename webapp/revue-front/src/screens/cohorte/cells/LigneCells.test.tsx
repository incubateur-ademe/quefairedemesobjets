import { fireEvent, screen, waitFor, within } from "@testing-library/react"

import type { GroupeActions } from "../../../api/mutations"
import { fakeApi, renderApp, setControlValue } from "../../../test-utils"
import { groupe, ligne } from "../fixtures"
import { parseCodes, parsePropositions, TargetCell } from "./LigneCells"

const CHOIX = {
  label_codes: {
    multiple: true,
    choix: [
      { value: "label_a", label: "Label A (label_a)" },
      { value: "label_b", label: "Label B (label_b)" },
    ],
  },
  proposition_service_codes: {
    multiple: true,
    actions: [
      { value: "donner", label: "Donner (donner)" },
      { value: "reparer", label: "Réparer (reparer)" },
    ],
    choix: [
      { value: "chaise", label: "Chaise (chaise)" },
      { value: "velo", label: "Vélo (velo)" },
    ],
  },
  statut: {
    multiple: false,
    choix: [
      { value: "ACTIF", label: "actif" },
      { value: "INACTIF", label: "inactif" },
    ],
  },
}

function edit(champ: string, actuel: string) {
  const upsertProposition = jest.fn().mockResolvedValue(undefined)
  const actions = { upsertProposition } as unknown as GroupeActions
  const api = fakeApi(() => CHOIX)
  const target = ligne(1, [champ], {
    correction: { actuel: { [champ]: actuel }, propose: null, etat: "valeur" },
  })
  renderApp(
    <TargetCell
      groupe={groupe(1)}
      ligne={target}
      modele="RevisionActeur"
      actions={actions}
    />,
    { api, url: "/data/revue/cohortes/7" },
  )
  fireEvent.click(screen.getByTitle("Proposer une valeur"))
  return { upsertProposition, target, api }
}

describe("TargetCell editing", () => {
  it("edits several codes with a multiple select, saved as a JSON list", async () => {
    const { upsertProposition, target } = edit("label_codes", '["label_a"]')
    const select = await screen
      .findByText("Label B (label_b)")
      .then((option) => option.closest("wa-select"))

    expect(select!.getAttribute("multiple")).not.toBeNull()
    setControlValue(select!, ["label_a", "label_b"])
    fireEvent.submit(select!.closest("form")!)

    expect(upsertProposition).toHaveBeenCalledWith(
      expect.anything(),
      target,
      "RevisionActeur",
      { label_codes: '["label_a","label_b"]' },
    )
  })

  it("edits a choice with a single select, keeping an unknown current value", async () => {
    const { upsertProposition } = edit("statut", "ANCIEN")
    const select = (await screen.findByText("inactif")).closest("wa-select")!

    expect(select.getAttribute("multiple")).toBeNull()
    expect(screen.getByText("ANCIEN")).toBeInTheDocument()
    setControlValue(select, "INACTIF")
    fireEvent.submit(select.closest("form")!)

    expect(upsertProposition.mock.calls[0][3]).toEqual({ statut: "INACTIF" })
  })

  it("keeps a text input for the other fields", async () => {
    const { api } = edit("nom", "Nom")

    await waitFor(() => expect(api.GET).toHaveBeenCalled())
    expect(document.querySelector('wa-input[label="nom"]')).not.toBeNull()
    expect(document.querySelector("wa-select")).toBeNull()
  })
})

describe("services editing", () => {
  const services = JSON.stringify([{ action: "reparer", sous_categories: ["velo"] }])
  const saved = (upsertProposition: jest.Mock) =>
    JSON.parse(upsertProposition.mock.calls[0][3].proposition_service_codes)

  it("edits the sous-catégories of an action and adds an action", async () => {
    const { upsertProposition } = edit("proposition_service_codes", services)
    await screen.findByText("+ Ajouter une action")

    setControlValue(screen.getByLabelText("Sous-catégories de l’action 1"), [
      "velo",
      "chaise",
    ])
    fireEvent.click(screen.getByText("+ Ajouter une action"))
    const action = screen.getByLabelText("Action 2")
    // An action is chosen once
    expect(within(action).queryByText("Réparer (reparer)")).toBeNull()
    setControlValue(action, "donner")
    setControlValue(screen.getByLabelText("Sous-catégories de l’action 2"), ["chaise"])
    fireEvent.submit(action.closest("form")!)

    expect(saved(upsertProposition)).toEqual([
      { action: "reparer", sous_categories: ["velo", "chaise"] },
      { action: "donner", sous_categories: ["chaise"] },
    ])
  })

  it("removes an action", async () => {
    const { upsertProposition } = edit("proposition_service_codes", services)

    fireEvent.click(await screen.findByTitle("Supprimer l’action 1"))
    expect(screen.queryByLabelText("Action 1")).toBeNull()
    fireEvent.submit(screen.getByText("+ Ajouter une action").closest("form")!)

    expect(saved(upsertProposition)).toEqual([])
  })
})

describe("parsePropositions", () => {
  it("reads the services, with single quotes; else nothing", () => {
    expect(parsePropositions("[{'action': 'a', 'sous_categories': ['b']}]")).toEqual([
      { action: "a", sous_categories: ["b"] },
    ])
    expect(parsePropositions("")).toEqual([])
    expect(parsePropositions("pas du json")).toEqual([])
  })
})

describe("parseCodes", () => {
  it("reads a JSON list, with single quotes, or a single code", () => {
    expect(parseCodes('["a", "b"]')).toEqual(["a", "b"])
    expect(parseCodes("['a']")).toEqual(["a"])
    expect(parseCodes("a")).toEqual(["a"])
    expect(parseCodes("")).toEqual([])
  })
})
